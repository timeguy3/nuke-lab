from litemapy import Schematic, Region, BlockState, TileEntity
from nbtlib.tag import Compound, String, Int, Byte, List


DIGITS = {
    0: ["111", "101", "101", "101", "111"],
    1: ["010", "110", "010", "010", "111"],
    2: ["111", "001", "111", "100", "111"],
    3: ["111", "001", "111", "001", "111"],
    4: ["101", "101", "111", "001", "001"],
    5: ["111", "100", "111", "001", "111"],
}


def b_state(name, **props):
    return BlockState(name, **{k: str(v) for k, v in props.items()})


def set_cmd_block(reg, x, y, z, cmd, chain=False, facing="south", auto=False):
    """Places a Command Block or Chain Command Block and attaches its NBT Command TileEntity."""
    block_id = "minecraft:chain_command_block" if chain else "minecraft:command_block"
    reg[x, y, z] = b_state(block_id, facing=facing, conditional="false")
    te_nbt = Compound({
        "id": String("minecraft:command_block"),
        "x": Int(x),
        "y": Int(y),
        "z": Int(z),
        "Command": String(cmd),
        "auto": Byte(1 if (chain or auto) else 0),
        "TrackOutput": Byte(1),
        "UpdateLastExecution": Byte(1),
    })
    reg.tile_entities.append(TileEntity(te_nbt))


def set_tnt_dispenser(reg, x, y, z, facing="down", registry_list=None):
    """Places a Dispenser pre-populated with TNT NBT and records its coords for the 1-click auto-filler."""
    reg[x, y, z] = b_state("minecraft:dispenser", facing=facing, triggered="false")
    items = List[Compound]()
    for slot in range(9):
        items.append(Compound({
            "Slot": Byte(slot),
            "id": String("minecraft:tnt"),
            "Count": Byte(64),
            "count": Int(64),
        }))
    te_nbt = Compound({
        "id": String("minecraft:dispenser"),
        "x": Int(x),
        "y": Int(y),
        "z": Int(z),
        "Items": items,
    })
    reg.tile_entities.append(TileEntity(te_nbt))
    if registry_list is not None:
        registry_list.append((x, y, z))


def draw_5chunk_depth_grid(reg, width_chunks=10):
    """
    Draws the 10-Chunk-Wide by 5-Chunk-Deep (160 x 80) Chunk Alignment Floor Grid at Y=0:
    - Chunk Z=0 (Z=0..15): Cyan Glass (Player Boardwalk & Carpet Control Deck, Level 31)
    - Chunk Z=1 (Z=16..31): Lime Glass (Active Shaping Chamber, Level 31)
    - Line Z=31..32: Yellow/Black Hazard Border (The Exact Lazy Chunk Stasis Line!)
    - Chunk Z=2 (Z=32..47): Orange Glass (Lazy Chunk Stasis Chamber, Level 32)
    - Chunks Z=3..4 (Z=48..79): Gray/Red Glass Downrange Target Impact Arena
    """
    cyan = b_state("minecraft:cyan_stained_glass")
    lime = b_state("minecraft:lime_stained_glass")
    orange = b_state("minecraft:orange_stained_glass")
    black_glass = b_state("minecraft:black_stained_glass")
    sea_lantern = b_state("minecraft:sea_lantern")
    yellow_c = b_state("minecraft:yellow_concrete")
    black_c = b_state("minecraft:black_concrete")
    slab = b_state("minecraft:smooth_stone_slab", type="bottom", waterlogged="false")

    for cx in range(width_chunks):
        base_x = cx * 16
        for dx in range(16):
            x = base_x + dx
            for z in range(80):
                is_border = (dx in (0, 15)) or (z % 16 in (0, 15))
                if z in (31, 32):
                    reg[x, 0, z] = yellow_c if (x + z) % 2 == 0 else black_c
                elif is_border:
                    reg[x, 0, z] = sea_lantern
                elif z < 16:
                    reg[x, 0, z] = cyan
                elif z < 31:
                    reg[x, 0, z] = lime
                elif z < 48:
                    reg[x, 0, z] = orange
                else:
                    reg[x, 0, z] = black_glass

            # Continuous Player Boardwalk across all stations at Y=1, Z=5..9
            for z in range(5, 10):
                reg[x, 1, z] = slab


def draw_floor_number(reg, x0, num):
    gold = b_state("minecraft:gold_block")
    black = b_state("minecraft:black_concrete")
    for r_idx, row in enumerate(DIGITS[num]):
        for c_idx, ch in enumerate(row):
            reg[x0 + 6 + c_idx, 0, 10 + r_idx] = gold if ch == "1" else black


def build_octagonal_shaping_chamber(reg, x0, center_z, dispenser_registry, include_center_shaper=False):
    """
    Builds the explosion-proof waterlogged Obsidian & Sub-Block Octagonal Shaping Basket
    around (X = x0 + 8, Z = center_z) and the 8-Point Octagonal Payload Dispenser Ring at Y=14.
    """
    obsidian = b_state("minecraft:obsidian")
    honey = b_state("minecraft:honey_block")
    smooth_stone = b_state("minecraft:smooth_stone")
    redstone_wire = b_state("minecraft:redstone_wire")
    water = b_state("minecraft:water", level="0")
    chest_n = b_state("minecraft:chest", facing="north", type="single", waterlogged="true")
    chest_s = b_state("minecraft:chest", facing="south", type="single", waterlogged="true")
    wall_wl = b_state("minecraft:cobblestone_wall", waterlogged="true")

    cx = x0 + 8

    # 1. Explosion-proof Obsidian Basin at Y=8..9 around (cx, center_z)
    for x in range(cx - 4, cx + 5):
        for z in range(center_z - 4, center_z + 3):
            reg[x, 8, z] = obsidian
            if x in (cx - 4, cx + 4) or z == center_z - 4:
                reg[x, 9, z] = obsidian

    # 2. Waterlogged Sub-Block Octagonal Alignment Ring around (cx, center_z) at Y=9
    subblock_ring = [
        (cx, center_z - 1, chest_s),
        (cx, center_z + 1, chest_n),
        (cx - 1, center_z, wall_wl),
        (cx + 1, center_z, wall_wl),
        (cx - 1, center_z - 1, honey),
        (cx + 1, center_z - 1, honey),
        (cx - 1, center_z + 1, honey),
        (cx + 1, center_z + 1, honey),
    ]
    for rx, rz, blk in subblock_ring:
        reg[rx, 9, rz] = blk

    # Central Obsidian Shaping Anvil + Water Source at (cx, Y=9..10, center_z) so blasts never break blocks
    reg[cx, 9, center_z] = obsidian
    reg[cx, 10, center_z] = water

    # 3. 8-Point Octagonal Payload Dispensers at Y=14 (3x3 hollow ring around cx, center_z)
    oct_ring_coords = [
        (cx - 1, center_z - 1), (cx, center_z - 1), (cx + 1, center_z - 1),
        (cx - 1, center_z),                         (cx + 1, center_z),
        (cx - 1, center_z + 1), (cx, center_z + 1), (cx + 1, center_z + 1),
    ]
    for dx, dz in oct_ring_coords:
        set_tnt_dispenser(reg, dx, 14, dz, facing="down", registry_list=dispenser_registry)
        reg[dx, 15, dz] = smooth_stone
        reg[dx, 16, dz] = redstone_wire

    # 4. Optional 9th Central Radial Shaping Dispenser at (cx, Y=14, center_z)
    if include_center_shaper:
        set_tnt_dispenser(reg, cx, 14, center_z, facing="down", registry_list=dispenser_registry)


def wire_boardwalk_lever_to_chamber(reg, x0, center_z, add_shaper_delay=False):
    """
    Wires the boardwalk lever at (X = x0 + 8, Y = 3, Z = 8) up to Y = 16 and South to center_z.
    If add_shaper_delay is True:
      - Fires the Central Shaping Dispenser IMMEDIATELY (at Tick 0).
      - Delays the 8 Outer Payload Ring Dispensers by 32 game ticks (16 redstone ticks = four 4-tick repeaters)
        so when the Central Shaping TNT explodes at Tick 80, the 8 outer Payload TNT still have 32 game ticks
        (1.6 seconds) of fuse left and get blasted radially outward into a 360-degree Nuke ring!
    """
    smooth_stone = b_state("minecraft:smooth_stone")
    redstone_wire = b_state("minecraft:redstone_wire")
    obs_up = b_state("minecraft:observer", facing="up", powered="false")
    obs_down = b_state("minecraft:observer", facing="down", powered="false")
    rep_1 = b_state("minecraft:repeater", facing="south", delay="1", locked="false", powered="false")
    rep_4 = b_state("minecraft:repeater", facing="south", delay="4", locked="false", powered="false")

    cx = x0 + 8

    # Boardwalk Lever Pedestal at (cx, Y=2..3, Z=8)
    reg[cx, 2, 8] = b_state("minecraft:emerald_block")
    reg[cx, 3, 8] = b_state("minecraft:lever", face="floor", facing="south", powered="false")
    reg[cx, 2, 9] = b_state("minecraft:note_block")

    # Observer vertical riser from Y=3 up to Y=15 at Z=9
    for y in range(3, 15):
        reg[cx, y, 9] = obs_up
    reg[cx, 15, 9] = smooth_stone
    reg[cx, 16, 9] = redstone_wire

    # Outer Payload Ring Spine along X = cx, Y = 15..16 from Z = 10 to center_z - 2
    for z in range(10, center_z - 1):
        reg[cx, 15, z] = smooth_stone
        if add_shaper_delay and z in (center_z - 6, center_z - 5, center_z - 4, center_z - 3):
            reg[cx, 16, z] = rep_4  # 4 x 4-tick repeaters = 16 redstone ticks (32 game ticks) payload delay
        elif z == 16:
            reg[cx, 16, z] = rep_1
        else:
            reg[cx, 16, z] = redstone_wire

    if add_shaper_delay:
        # Fast Zero-Delay Parallel Line along X = cx - 3, Y = 17..18 straight to the Central Shaping Dispenser
        for x in range(cx - 3, cx + 1):
            reg[x, 17, 10] = smooth_stone
            reg[x, 18, 10] = redstone_wire
            reg[x, 17, center_z] = smooth_stone
            reg[x, 18, center_z] = redstone_wire
        reg[cx, 16, 10] = redstone_wire
        reg[cx, 17, 10] = smooth_stone  # Ensure signal steps up to Y=18 at Z=10
        reg[cx - 3, 16, 10] = obs_up
        reg[cx - 3, 15, 10] = b_state("minecraft:note_block")
        reg[cx - 2, 15, 10] = smooth_stone
        reg[cx - 2, 16, 10] = redstone_wire
        reg[cx - 1, 15, 10] = smooth_stone
        reg[cx - 1, 16, 10] = redstone_wire

        for z in range(10, center_z + 1):
            reg[cx - 3, 17, z] = smooth_stone
            if z == 20:
                reg[cx - 3, 18, z] = rep_1
            else:
                reg[cx - 3, 18, z] = redstone_wire

        # Drop fast signal straight down into the Central Shaping Dispenser at (cx, Y=14, center_z)
        reg[cx, 17, center_z] = b_state("minecraft:note_block")
        reg[cx, 16, center_z] = obs_down
        reg[cx, 15, center_z] = obs_down


def add_stage_1_seeding(reg, x0, dispenser_registry):
    """STAGE 1 (X=16..31): Pure 8-Point Sub-Block Octagonal Payload Seeding at Z=22."""
    build_octagonal_shaping_chamber(reg, x0, center_z=22, dispenser_registry=dispenser_registry, include_center_shaper=False)
    wire_boardwalk_lever_to_chamber(reg, x0, center_z=22, add_shaper_delay=False)


def add_stage_2_radial_blast(reg, x0, dispenser_registry):
    """STAGE 2 (X=48..63): Stage 1 + Central Radial Shaping Charge at Z=22 (Full 360-degree mid-air Nuke ring bloom!)."""
    build_octagonal_shaping_chamber(reg, x0, center_z=22, dispenser_registry=dispenser_registry, include_center_shaper=True)
    wire_boardwalk_lever_to_chamber(reg, x0, center_z=22, add_shaper_delay=True)


def add_stage_3_lazy_sweeper(reg, x0, dispenser_registry):
    """
    STAGE 3 (X=80..95): Stage 2 Hardware placed at Z=29 + High-Speed Slime Sweeper & Lazy Chunk Stasis Chamber at Z=32..36.
    Right as the central shaping charge blasts the 8 payload TNT radially outward at Tick 80gt,
    the Slime Sweeper pushes the expanding ring across Z=31 -> Z=32 into the Orange Lazy Chunk!
    Also includes a Boardwalk 'WAKE UP LAZY CHUNK' button that promotes Z=32..47 so you can watch the frozen ring bloom on command!
    """
    obsidian = b_state("minecraft:obsidian")
    honey = b_state("minecraft:honey_block")
    slime = b_state("minecraft:slime_block")
    smooth_stone = b_state("minecraft:smooth_stone")
    redstone_wire = b_state("minecraft:redstone_wire")
    sticky_s = b_state("minecraft:sticky_piston", facing="south", extended="false")
    obs_s = b_state("minecraft:observer", facing="south", powered="false")
    obs_down = b_state("minecraft:observer", facing="down", powered="false")
    rep_4_s = b_state("minecraft:repeater", facing="south", delay="4", locked="false", powered="false")
    rep_2_e = b_state("minecraft:repeater", facing="east", delay="2", locked="false", powered="false")

    cx = x0 + 8

    # 1. Build Octagonal Shaping Chamber at Z=29 (2 blocks North of the Z=32 Lazy Chunk border)
    build_octagonal_shaping_chamber(reg, x0, center_z=29, dispenser_registry=dispenser_registry, include_center_shaper=True)
    wire_boardwalk_lever_to_chamber(reg, x0, center_z=29, add_shaper_delay=True)

    # 2. Build Orange Lazy Chunk Stasis Catch Chamber at Z=32..36, Y=8..13
    for x in range(cx - 4, cx + 5):
        for z in range(32, 37):
            reg[x, 8, z] = obsidian
            if x in (cx - 4, cx + 4) or z == 36:
                for y in range(9, 14):
                    reg[x, y, z] = obsidian
    # Honey alignment backstop at Z=34 inside the Lazy Chunk so swept TNT freezes right at Z=32..33
    for x in range(cx - 3, cx + 4):
        reg[x, 9, 34] = honey
        reg[x, 10, 34] = honey

    # 3. High-Speed Slime Sweeper Piston Wall at Y=10..11, Z=25..27 pushing South toward Z=32
    for x in range(cx - 2, cx + 3):
        reg[x, 10, 25] = obs_s
        reg[x, 10, 26] = sticky_s
        reg[x, 10, 27] = slime

    # 4. Precision 41-Redstone-Tick Delay Line along X = cx + 3 so the Sweeper fires 1 tick AFTER the shaping blast (Tick 80gt)
    for z in range(11, 25):
        reg[cx + 3, 15, z] = smooth_stone
        if 12 <= z <= 21:
            reg[cx + 3, 16, z] = rep_4_s  # 10 x 4-tick repeaters = 40 redstone ticks (80 game ticks)
        else:
            reg[cx + 3, 16, z] = redstone_wire
    # Tap signal from Z=11 main spine over to X = cx + 3
    for x in range(cx + 1, cx + 4):
        reg[x, 15, 11] = smooth_stone
        reg[x, 16, 11] = redstone_wire
    reg[cx + 2, 16, 11] = rep_2_e  # +1 redstone tick (2gt) so sweep happens right after shaping detonation

    # Drop signal down to Y=10, Z=24 behind the Sweeper Observers
    reg[cx + 3, 15, 24] = b_state("minecraft:note_block")
    for y in range(11, 15):
        reg[cx + 3, y, 24] = obs_down
    for x in range(cx - 2, cx + 4):
        reg[x, 9, 24] = smooth_stone
        reg[x, 10, 24] = redstone_wire

    # 5. Add Boardwalk Button to WAKE UP / RE-FREEZE this Lazy Chunk on Command!
    reg[x0 + 4, 2, 8] = b_state("minecraft:orange_concrete")
    reg[x0 + 4, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    set_cmd_block(
        reg, x0 + 4, 1, 8,
        "execute Positioned ~ ~ ~ run forceload add ~-4 ~24 ~11 ~39",
        chain=False, facing="down"
    )
    # Button next to it to Re-Lock Z=32..47 back to Lazy Level 32 after testing
    reg[x0 + 2, 2, 8] = b_state("minecraft:cyan_concrete")
    reg[x0 + 2, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    set_cmd_block(
        reg, x0 + 2, 1, 8,
        "execute Positioned ~ ~ ~ run forceload remove ~-2 ~24 ~13 ~39",
        chain=False, facing="down"
    )


def add_stage_4_multi_ring_stacker(reg, x0, dispenser_registry):
    """
    STAGE 4 (X=112..127): Stage 3 Hardware + 3-Cycle Multi-Ring Pulse Stacker & Cross-Border Shaping Trim.
    Pulling the lever runs 3 consecutive cycles, sweeping 24 primed TNT (3 concentric rings of 8 TNT)
    into the Lazy Chunk and applying stepped radial impulses so Ring 1 = Outer, Ring 2 = Middle, Ring 3 = Inner!
    """
    add_stage_3_lazy_sweeper(reg, x0, dispenser_registry)

    smooth_stone = b_state("minecraft:smooth_stone")
    redstone_wire = b_state("minecraft:redstone_wire")
    rep_4_e = b_state("minecraft:repeater", facing="east", delay="4", locked="false", powered="false")
    rep_4_w = b_state("minecraft:repeater", facing="west", delay="4", locked="false", powered="false")

    cx = x0 + 8

    # Build a 3-Pulse Multi-Ring Delay Loop on the platform at Y=15..16, Z=10..13
    for x in range(x0 + 2, cx + 1):
        for z in range(10, 14):
            reg[x, 15, z] = smooth_stone
    for x in range(x0 + 3, cx):
        reg[x, 16, 11] = rep_4_w
        reg[x, 16, 13] = rep_4_e
    reg[x0 + 2, 16, 11] = redstone_wire
    reg[x0 + 2, 16, 12] = redstone_wire
    reg[x0 + 2, 16, 13] = redstone_wire

    # Cross-Border Radial Shaping Trim Dispenser at Z=31 (Active Chunk edge) to step the concentric ring radii
    set_tnt_dispenser(reg, cx, 11, 31, facing="south", registry_list=dispenser_registry)


def add_stage_5_full_nuke_launcher(reg, x0, dispenser_registry):
    """
    STAGE 5 (X=144..159): Full Working Nuke Payload Builder + Cross-Border Propellant Accelerator +
    Survival Portal Chunk Loaders + Downrange Target Bullseye Arena at Z=64!
    """
    add_stage_4_multi_ring_stacker(reg, x0, dispenser_registry)

    obsidian = b_state("minecraft:obsidian")
    portal_x = b_state("minecraft:nether_portal", axis="x")
    smooth_stone = b_state("minecraft:smooth_stone")
    redstone_wire = b_state("minecraft:redstone_wire")
    red_c = b_state("minecraft:red_concrete")
    white_c = b_state("minecraft:white_concrete")
    sea_lantern = b_state("minecraft:sea_lantern")

    cx = x0 + 8

    # 1. Remove the Z=34 honey backstop wall in Stage 5's Lazy Chamber so the Nuke has a clear flight path South to Z=64!
    for x in range(cx - 3, cx + 4):
        for z in range(33, 37):
            for y in range(9, 14):
                reg[x, y, z] = b_state("minecraft:air")
    # Place a low waterlogged obsidian catch lip at Y=8, Z=32..34 so frozen TNT sits at Y=9, Z=32.5 ready for launch
    for x in range(cx - 3, cx + 4):
        for z in range(32, 35):
            reg[x, 8, z] = obsidian

    # 2. Cross-Border Main +Z Propellant Accelerator Array at Z=31, Y=10 (Inside Active Lime Chunk right behind Z=32)
    # Detonating batches here pushes the frozen Nuke rings in Z=32 South toward the Target Bullseye at Z=64!
    for x in range(cx - 2, cx + 3):
        set_tnt_dispenser(reg, x, 10, 31, facing="south", registry_list=dispenser_registry)
        reg[x, 11, 31] = smooth_stone
        reg[x, 12, 31] = redstone_wire

    # Boardwalk Button B (Blue Concrete at X=x0+6, Z=8): "FIRE PROPELLANT BATCH (+Z VELOCITY)"
    reg[x0 + 6, 2, 8] = b_state("minecraft:blue_concrete")
    reg[x0 + 6, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    for z in range(8, 32):
        reg[x0 + 6, 11, z] = smooth_stone
        if z == 20:
            reg[x0 + 6, 12, z] = b_state("minecraft:repeater", facing="south", delay="1", locked="false", powered="false")
        else:
            reg[x0 + 6, 12, z] = redstone_wire
    # Vertical observer link from Button B (Y=2, Z=8) up to Propellant line (Y=12, Z=8)
    obs_up = b_state("minecraft:observer", facing="up", powered="false")
    reg[x0 + 6, 2, 9] = b_state("minecraft:note_block")
    for y in range(3, 12):
        reg[x0 + 6, y, 9] = obs_up

    # 3. Boardwalk Button C (Red Concrete at X=x0+4, Z=8): "PROMOTE CHUNK & LAUNCH NUKE TO TARGET!"
    # Promotes Z=32..79 to Entity-Processing so the frozen Nuke wakes up, flies South to Z=64, and blooms into 3 rings!
    set_cmd_block(
        reg, x0 + 4, 1, 8,
        "execute Positioned ~ ~ ~ run forceload add ~-4 ~24 ~11 ~71",
        chain=False, facing="down"
    )

    # 4. Survival Nether Portal Chunk Loader Frame (at Z=2) & Secondary Release Portal Frame (at Z=44)
    for z_portal in (2, 44):
        for x in range(x0 + 1, x0 + 5):
            reg[x, 1, z_portal] = obsidian
            reg[x, 5, z_portal] = obsidian
        for y in range(1, 6):
            reg[x0 + 1, y, z_portal] = obsidian
            reg[x0 + 4, y, z_portal] = obsidian
    for x in range(x0 + 2, x0 + 4):
        for y in range(2, 5):
            reg[x, y, 2] = portal_x

    # 5. Downrange Target Bullseye Platform centered at (X = cx, Z = 64, Y = 1)
    for x in range(x0 - 8, x0 + 16):
        for z in range(50, 78):
            if 0 <= x < 160 and 0 <= z < 80:
                dist = int(((x - cx) ** 2 + (z - 64) ** 2) ** 0.5)
                if dist <= 12:
                    if dist == 0:
                        reg[x, 1, z] = sea_lantern
                    elif dist % 3 == 0:
                        reg[x, 1, z] = red_c
                    else:
                        reg[x, 1, z] = white_c


def build_station_0_carpet_command_deck(reg, dispenser_registry):
    """
    STATION 0 (Chunk X=0, X=0..15, Z=0..15):
    Builds the Carpet Mod & Vanilla Command Block Control Deck using relative (~dx ~dy ~dz) coordinates
    so every button works at ANY world coordinate aligned to chunk borders!
    """
    # Origin Beacon Marker at (0, 0, 0)
    diamond = b_state("minecraft:diamond_block")
    gold = b_state("minecraft:gold_block")
    beacon = b_state("minecraft:beacon")
    for x in range(3):
        for z in range(3):
            reg[x, 0, z] = diamond
    reg[0, 1, 0] = gold
    reg[0, 2, 0] = beacon

    draw_floor_number(reg, 0, 0)

    # BUTTON 1 (X=3, Y=3, Z=8, Emerald Block): INITIALIZE LAB, SET CARPET LAZY CHUNK RULES & AUTO-FILL ALL TNT
    reg[3, 2, 8] = b_state("minecraft:emerald_block")
    reg[3, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")

    # Impulse Command Block at (3, 1, 8) + Chain Command Blocks running East along Y=1, Z=8 and Z=7
    init_commands = [
        "carpet creativePlayersLoadChunks false",
        "carpet optimizedFastEntityMovement true",
        "forceload remove all",
        "execute Positioned ~ ~ ~ run forceload add ~-3 ~-8 ~156 ~23",
        'tellraw @a {"text":"[OSC Nuke Lab] Creative Players Chunk-Loading DISABLED! Chunks Z=0..31 are Active (Level 31); Orange Chunks Z=32..47 are now Lazy (Level 32)! All Dispensers filled with 64 TNT!","color":"green"}',
    ]
    # Add relative `/item replace block` commands for every dispenser in the entire lab so 1 click fills them all!
    for idx, (dx, dy, dz) in enumerate(dispenser_registry):
        # We place the chain along a snake or run `/item replace` relative to each chain block's own coordinates
        pass

    # Place main initialization chain going South along X=3, Y=1, Z=8..12
    for i, cmd in enumerate(init_commands):
        cz = 8 + i
        set_cmd_block(reg, 3, 1, cz, cmd, chain=(i > 0), facing="south", auto=(i > 0))
        if i == 3:
            # Adjust relative coordinate offset since this command block sits at (3, 1, 11)
            set_cmd_block(
                reg, 3, 1, cz,
                "forceload add ~-3 ~-11 ~156 ~20",
                chain=True, facing="south", auto=True
            )

    # Dedicated "AUTO-FILL ALL DISPENSERS WITH TNT" Button at (X=5, Y=3, Z=8, TNT / Red Wool Pedestal)
    reg[5, 2, 8] = b_state("minecraft:red_wool")
    reg[5, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    # Build vertical/horizontal chain from (5, 1, 8) going South Z=8..70 at Y=1 to fill every dispenser via relative coords
    for i, (tx, ty, tz) in enumerate(dispenser_registry):
        cz = 8 + i
        if cz < 78:
            rel_x = tx - 5
            rel_y = ty - 1
            rel_z = tz - cz
            cmd = f"item replace block ~{rel_x} ~{rel_y} ~{rel_z} container.0 with minecraft:tnt 64"
            set_cmd_block(reg, 5, 1, cz, cmd, chain=(i > 0), facing="south", auto=(i > 0))

    # BUTTON 2 (X=7, Y=3, Z=8, Gold Block): INSPECT NEAREST FROZEN TNT NBT (Velocity Vector & Fuse)
    reg[7, 2, 8] = gold
    reg[7, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    set_cmd_block(
        reg, 7, 1, 8,
        'execute as @e[type=minecraft:tnt,sort=nearest,limit=3] run tellraw @a [{"text":"[TNT Telemetry] ","color":"gold"},{"entity":"@s","nbt":"Pos"},{"text":" | Motion: ","color":"aqua"},{"entity":"@s","nbt":"Motion"},{"text":" | Fuse: ","color":"yellow"},{"entity":"@s","nbt":"Fuse"}]',
        chain=False, facing="south"
    )

    # BUTTON 3 (X=9, Y=3, Z=8, Blue Ice): TOGGLE /tick freeze
    reg[9, 2, 8] = b_state("minecraft:blue_ice")
    reg[9, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    set_cmd_block(reg, 9, 1, 8, "tick freeze", chain=False, facing="south")

    # BUTTON 4 (X=11, Y=3, Z=8, Copper Block): STEP +1 GAME TICK (/tick step 1t)
    reg[11, 2, 8] = b_state("minecraft:copper_block")
    reg[11, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    set_cmd_block(reg, 11, 1, 8, "tick step 1t", chain=False, facing="south")

    # BUTTON 5 (X=13, Y=3, Z=8, Obsidian): KILL ALL FLOATING TNT & RESET ARENA
    reg[13, 2, 8] = b_state("minecraft:obsidian")
    reg[13, 3, 8] = b_state("minecraft:stone_button", face="floor", facing="south", powered="false")
    set_cmd_block(reg, 13, 1, 8, "kill @e[type=minecraft:tnt]", chain=False, facing="south")
    set_cmd_block(
        reg, 13, 1, 9,
        "carpet creativePlayersLoadChunks true",
        chain=True, facing="south", auto=True
    )


def generate_master_carpet_lab():
    reg = Region(0, 0, 0, 160, 30, 80)
    dispenser_registry = []

    draw_5chunk_depth_grid(reg, width_chunks=10)

    # Build Cumulative Stations 1 to 5 spaced every 2 Chunks along X
    stations = [
        (1, 16, add_stage_1_seeding),
        (2, 48, add_stage_2_radial_blast),
        (3, 80, add_stage_3_lazy_sweeper),
        (4, 112, add_stage_4_multi_ring_stacker),
        (5, 144, add_stage_5_full_nuke_launcher),
    ]

    for stage_num, x0, builder_fn in stations:
        draw_floor_number(reg, x0, stage_num)
        builder_fn(reg, x0, dispenser_registry)

    # Build Station 0 Carpet Command Deck last so it registers every dispenser's coordinates for 1-click auto-filling
    build_station_0_carpet_command_deck(reg, dispenser_registry)

    schem = reg.as_schematic(
        name="OSC Nuke Carpet Master Lab (Steps 1-5)",
        author="OSC Builder",
        description="Paste at (X%16==0, Z%16==0). Includes Carpet Mod Command Deck, 5 Cumulative Nuke Stages, Lazy Chunk Stasis Chamber, and Target Arena.",
    )
    schem.save("osc_nuke_carpet_master_lab.litematic")
    print(f"Saved osc_nuke_carpet_master_lab.litematic with {len(dispenser_registry)} pre-loaded TNT dispensers!")


if __name__ == "__main__":
    generate_master_carpet_lab()
