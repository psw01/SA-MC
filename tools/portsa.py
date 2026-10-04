#!/usr/bin/env python3
"""Port SACraft (SA SE) to GTA San Andreas, in place.

What the port is, and what it deliberately is not:

* The shared-memory protocol does **not** change.  Same magic ("SKYC"), same
  version (11), same byte layout, same mapping name (Local\\SkyCraft_v1).  That
  is the single most important decision in this file: it means the Minecraft mod
  is carried over nearly verbatim and only its *vocabulary* changes.  A later
  commit can rename the mapping once both halves ship together.
* The SA half (skse/) is deleted outright.  SA replaces it with a wholly new
  RenderWare / DirectX9 host under sa/, which this script never writes to.
* Everything else -- the Fabric mod, the dev tools, the packaging, the docs --
  is rewritten by the rules below.

The rules are data, not code sprinkled through the tree, so the whole port can
be audited in one read and re-run deterministically.

Usage:
    python3 tools/portsa.py            # rewrite the tree in place
    python3 tools/portsa.py --check    # report what would change; write nothing
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------------------
# scope
# --------------------------------------------------------------------------------------

# Never rewritten.  THIRD-PARTY-NOTICES.md still credits CommonLibSSE-NG and friends,
# which we no longer build against but which this project descends from; docs/DESIGN.md
# is the upstream design record and stays as written.
KEEP = {
    Path("THIRD-PARTY-NOTICES.md"),
    Path("docs/DESIGN.md"),
    Path("LICENSE"),
}

# Binary or generated: skip.
SKIP_SUFFIXES = {".jpg", ".png", ".jar", ".zip", ".ico", ".ttf"}


def in_scope(rel: Path) -> bool:
    p = rel.as_posix()
    if rel in KEEP:
        return False
    if p.startswith(("sa/", ".refs/", "dist/", ".tools/")):
        return False
    if any(part in {".git", "__pycache__", ".gradle", "build"} for part in rel.parts):
        return False
    return rel.suffix.lower() not in SKIP_SUFFIXES


# --------------------------------------------------------------------------------------
# rule tables
# --------------------------------------------------------------------------------------

# Exact replacements, applied first, longest/most specific first.  These carry meaning a
# blind word swap cannot express: scale factors, damage curves, renamed properties.
LITERAL: list[tuple[str, str]] = [
    # ---- Minecraft mod identity --------------------------------------------------------
    ('"id": "sacraft"', '"id": "sacraft"'),
    ("package dev.sacraft;", "package dev.sacraft;"),
    ("dev.sacraft.", "dev.sacraft."),
    ("group=dev.sacraft", "group=dev.sacraft"),
    ('"name": "SACraft"', '"name": "SACraft"'),
    ('mod_id=sacraft', 'mod_id=sacraft'),
    ("archivesName = 'sacraft'", "archivesName = 'sacraft'"),
    ("rootProject.name = 'sacraft'", "rootProject.name = 'sacraft'"),

    # ---- the bundled launcher instance --------------------------------------------------
    ("--launch SACraft", "--launch SACraft"),
    ("%LOCALAPPDATA%\\SACraft", "%LOCALAPPDATA%\\SACraft"),
    ("%LOCALAPPDATA/SACraft", "%LOCALAPPDATA/SACraft"),
    ("SACraft world", "SACraft world"),
    ("SACraft instance", "SACraft instance"),

    # ---- scale --------------------------------------------------------------------------
    # 70 units/block came from SA's ~128-unit-tall player against MC's 1.8 blocks.
    # In GTA III-eraRenderWare one world unit is one foot and CJ stands about 6 of them,
    # against MC's 1.8 blocks => 1 block ~= 3.33 ft.  We use 30 units/block and treat a
    # unit as 4 inches, which keeps a block at roughly a metre and matches how the L4C
    # port picked 40 units/block off the same reasoning (survivor hull 72 units tall).
    ("kUnitsPerBlock = 30.0", "kUnitsPerBlock = 30.0"),
    ("UNITS_PER_BLOCK = 30.0", "UNITS_PER_BLOCK = 30.0"),
    ("unitsPerBlock = 30.0", "unitsPerBlock = 30.0"),
    ("1 Minecraft block == 30 San Andreas units. SA's collision scale is feet-ish and CJ is
        // roughly 6 units tall against Minecraft's 1.8 blocks; 30 keeps a block near a metre.
        // Pin this in-game before shipping: see docs/PORTING-SA.md.",
     "1 Minecraft block == 30 San Andreas units. SA's collision scale is feet-ish and CJ is\n"
     "        // roughly 6 units tall against Minecraft's 1.8 blocks; 30 keeps a block near a metre.\n"
     "        // Pin this in-game before shipping: see docs/PORTING-SA.md."),
    ("(about a metre)", "(about a metre)"),

    # ---- vertical range -------------------------------------------------------------------
    ("San Andreas spans about 4000 feet vertically (Chiliad's summit to the ocean floor),
which at 30 units per block is roughly 130 blocks - inside Minecraft's default build height.",
     "San Andreas spans about 4000 feet vertically (Chiliad's summit to the ocean floor),\n"
     "which at 30 units per block is roughly 130 blocks - inside Minecraft's default build height."),

    # ---- damage scaling --------------------------------------------------------------------
    # SA bandits sit at 50-300 HP; an SA pedestrian dies to single-digit bullets, so
    # the incoming divisor drops and the outgoing multiplier must too, or a wooden sword
    # insta-kills the whole of Los Santos.
    ("multiplied by `2 + 0.1 × NPC level`", "multiplied by `2 + 0.1 × NPC level`"),
    ("divided by 2, so a 20-damage SA hit becomes 10 MC damage (5 hearts)",
     "divided by 2, so a 20-damage SA hit becomes 10 MC damage (5 hearts)"),
    ("a diamond sword crit of ~10 hits a level-10 ped for ~25",
     "a diamond sword crit of ~10 hits a level-10 ped for ~25"),

    # ---- link names used by the dev stand-ins ----------------------------------------------
    ('NAME = r"Local\\SkyCraft_v1"', 'NAME = os.environ.get("SACRAFT_LINK", r"Local\\SkyCraft_v1")'),
    ('NAME = "Local\\SkyCraft_v1"', 'NAME = os.environ.get("SACRAFT_LINK", r"Local\\SkyCraft_v1")'),
    ('tagname="Local\\\\SkyCraft_v1"', 'tagname=os.environ.get("SACRAFT_LINK", "Local\\\\SkyCraft_v1")'),
    ('os.environ.get("SKYCRAFT_LINK", "Local\\\\SkyCraft_v1")  # fake_guest.py runs one beside a real SA',
     'os.environ.get("SACRAFT_LINK", "Local\\\\SkyCraft_v1")  # fake_guest.py runs one beside a real host'),
    ('os.environ.get("SKYCRAFT_LINK", "Local\\\\SkyCraft_v1")',
     'os.environ.get("SACRAFT_LINK", "Local\\\\SkyCraft_v1")'),
    ('SACRAFT_DEPLOY_DIR', 'SACRAFT_DEPLOY_DIR'),

    # ---- protocol field meanings that move to SA -------------------------------------------
    ("std::uint32_t worldId;         // exterior: SA interior index + 1; 0: the main map",
     "std::uint32_t worldId;         // exterior: SA interior index + 1; 0: the main map"),
    ("double        posX, posY, posZ;  // the host player's feet, MC coords",
     "double        posX, posY, posZ;  // the host player's feet, MC coords"),
    ("float         gameHour;      // SA clock, 0..23", "float         gameHour;      // SA clock, 0..23      // SA clock, 0..23"),
    ("std::uint32_t saPid;   // the host game's pid (field name is protocol history)", "std::uint32_t saPid;   // the host game's pid (field name is protocol history)   // the host game's pid (field name is protocol history)"),
    ("std::uint64_t saHeartbeatMs;  // GetTickCount64() at last host frame",
     "std::uint64_t saHeartbeatMs;  // GetTickCount64() at last host frame"),
    ("std::uint32_t mcHeartbeatMs;      // GetTickCount64() at last MC frame",
     "std::uint32_t mcHeartbeatMs;      // GetTickCount64() at last MC frame"),
    ("// All multi-byte values are little-endian. The host game creates the mapping; Minecraft opens it.",
     "// All multi-byte values are little-endian. The host game creates the mapping; Minecraft opens it."),
    ("// Coordinates in this protocol are always Minecraft space (blocks, Y up, Z south) unless noted.
// The host's own space differs per game: SA is Z-up right-handed, SA is Z-up left-handed.",
     "// Coordinates in this protocol are always Minecraft space (blocks, Y up, Z south) unless noted.
// The host's own space differs per game: SA is Z-up right-handed, SA is Z-up left-handed.\n"
     "// The host's own space differs per game: SA is Z-up right-handed, SA is Z-up left-handed."),
    ("// SACraft shared-memory protocol (game host plugin <-> Minecraft Fabric mod).
// Ported to GTA San Andreas: the host is sa/sacraft.dll (RenderWare/DX9), not skse/.",
     "// SACraft shared-memory protocol (game host plugin <-> Minecraft Fabric mod).\n"
     "// Ported to GTA San Andreas: the host is sa/sacraft.dll (RenderWare/DX9), not skse/."),
    ("// This header is the single source of truth for the byte layout. The Java side mirrors it in\n"
     "// fabric/src/main/java/dev/skycraft/link/Proto.java; if you change anything here, change it\n"
     "// there too and bump kVersion.",
     "// This header is the single source of truth for the byte layout. The Java side mirrors it in\n"
     "// fabric/src/main/java/dev/sacraft/link/Proto.java; if you change anything here, change it\n"
     "// there too and bump kVersion.\n"
     "//\n"
     "// THE PORT RULE: bringing SACraft onto a new game must not touch this file. Every byte\n"
     "// offset, struct size and message type below is shared by the unmodified Minecraft mod, so\n"
     "// a port writes a new host against these numbers instead of editing them. Renaming the\n"
     "// mapping itself is a coordinated change to both halves and belongs after the mod ships."),
    ("enum HurtKind : std::uint16_t  // how the host's hit landed", "enum HurtKind : std::uint16_t  // how the host's hit landed  // how the host's hit landed"),
    ("kHurtMagic = 2,   // SA: an explosion, a run-over, a fall from a vehicle", "kHurtMagic = 2,   // SA: an explosion, a run-over, a fall from a vehicle   // SA: an explosion, a run-over, a fall from a vehicle"),
    ("kHurtBlockedInSA = 1u << 0,  // the host soaked part of it (SA: armour)", "kHurtBlockedInSA = 1u << 0,  // the host soaked part of it (SA: armour)  // the host soaked part of it (SA: armour)"),
    ("kHurtPowerAttack = 1u << 1,      // SA: a melee special/kick", "kHurtPowerAttack = 1u << 1,      // SA: a melee special/kick      // SA: a melee special/kick"),
    ("b = attacker id (SA: an entity index)", "b = attacker id (SA: an entity index)"),
    ("entityIndex = the host's skill id. SA used ActorValues (9 Block,",
     "entityIndex = the host's skill id. SA used ActorValues (9 Block,"),
    ("10 Smithing, 11 Heavy Armor, 12 Light Armor); SA has no skill system, so its host
// treats these as plain counters driving wanted-level and stats",
     "10 Smithing, 11 Heavy Armor, 12 Light Armor); SA has no skill system, so its host\n"
                                    "// treats these as plain counters driving wanted-level and stats"),
    ("// Nearby host actors (SA: CPed), mirrored in Minecraft as invisible hittable proxies.",
     "// Nearby host actors (SA: CPed), mirrored in Minecraft as invisible hittable proxies."),
    ("char          name[24];    // display name, UTF-8, NUL-terminated (truncated).
                                   // SA has no per-ped name: the host sends the ped model name",
     "char          name[24];    // display name, UTF-8, NUL-terminated (truncated).
                                   // SA has no per-ped name: the host sends the ped model name.\n"
     "                                   // SA has no per-ped name: the host sends the ped model name"),
    ("float         healthFrac;  // 0..1 (SA: CPed::m_fHealth / 1000)", "float         healthFrac;  // 0..1 (SA: CPed::m_fHealth / 1000) (SA: CPed::m_fHealth / 1000)"),
    ("std::uint16_t level;     // SA: derived from ped type + wanted level", "std::uint16_t level;     // SA: derived from ped type + wanted level     // SA: derived from ped type + wanted level"),
    ("kActorEssential = 1u << 2,  // SA: a mission-critical ped (CVector hack)", "kActorEssential = 1u << 2,  // SA: a mission-critical ped (CVector hack)  // SA: a mission-critical ped (CVector hack)"),
    ("// The host's water (SA: oceans, rivers, canals, pools) around the player, for Minecraft to treat as its own",
     "// The host's water (SA: oceans, rivers, canals, pools) around the player, for Minecraft to treat as its own"),
    ("std::uint32_t worldId;           // as in SkyState", "std::uint32_t worldId;           // as in SkyState"),
    ("// What a piece of diggable SA geometry is made of, as the Minecraft block it digs into\n"
     "// (ColTri flags bits 8-15). Chosen on the SA side from BulletAI materials and object types.",
     "// What a piece of diggable host geometry is made of, as the Minecraft block it digs into\n"
     "// (ColTri flags bits 8-15). The host picks it per triangle: SA gives every atomic object a\n"
     "// surface/material id, and terrain chunks know whether they are sand, dirt or road."),
    ("kDigNone = 0,   // not known: concrete (SA's default building material)", "kDigNone = 0,   // not known: concrete (SA's default building material)"),
    ("kDigGrass = 1,   // SA: the low-detail countryside ground chunks", "kDigGrass = 1,   // SA: the low-detail countryside ground chunks   // SA: the low-detail countryside ground chunks"),
    ("kDigSand = 7,    // SA: beach tiles and the desert", "kDigSand = 7,    // SA: beach tiles and the desert    // SA: beach tiles and the desert"),
    ("kDigMetal = 14,  // SA: vehicles, girders, chain-link posts", "kDigMetal = 14,  // SA: vehicles, girders, chain-link posts  // SA: vehicles, girders, chain-link posts"),
    ("kDigBedrock = 21,  // Minecraft only: a few blocks under the land (SA's map bottom)",
     "kDigBedrock = 21,  // Minecraft only: a few blocks under the land (SA's map bottom) (SA's map bottom)"),
    ("// Exact host collision triangle (MC space) for the player's smooth collider.
// SA hands over RenderWare triangles straight from the collision model - no BulletAI
// heightfields to decode, which is why this port's stage C was easy.",
     "// Exact host collision triangle (MC space) for the player's smooth collider.\n"
     "// SA hands over RenderWare triangles straight from the collision model - no BulletAI\n"
     "// heightfields to decode, which is why this port's stage C was easy."),
    ("kTriStairHelper = 1u << 0,  // an invisible helper ramp (SA's stairs/ramps): walkable, never a wall",
     "kTriStairHelper = 1u << 0,  // an invisible helper ramp (SA's stairs/ramps): walkable, never a wall"),
    ("kTriDiggable = 1u << 1,     // terrain, buildings, objects: can be dug into (bits 8-15: DigMaterial).",
     "kTriDiggable = 1u << 1,     // terrain, buildings, objects: can be dug into (bits 8-15: DigMaterial)."),
    ("// not collision, only for telling what's inside the host's geometry",
     "// not collision, only for telling what's inside the host's geometry"),
    ("kTriTerrain = 1u << 3,      // the land (SA: a terrain chunk, already triangles)",
     "kTriTerrain = 1u << 3,      // the land (SA: a terrain chunk, already triangles)"),
    ("// Replaces all host collision inside the inclusive block box [min, max].",
     "// Replaces all host collision inside the inclusive block box [min, max]."),
    ("// Byte ring like the collision ring. Minecraft ships its own block meshes (built by Minecraft's",
     "// Byte ring like the collision ring. Minecraft ships its own block meshes (built by Minecraft's"),
    ("// block renderer: models, tint, AO, lighting) and its block atlas; the host draws them in its own",
     "// block renderer: models, tint, AO, lighting) and its block atlas; the host draws them in its own"),
    ("// frame so blocks stay locked to the world and are occluded by host geometry.",
     "// frame so blocks stay locked to the world and are occluded by host geometry."),
    ("// Raw 20 Hz physics ticks, so the host can interpolate on its own frame clock exactly like",
     "// Raw 20 Hz physics ticks, so the host can interpolate on its own frame clock exactly like"),
    ("// the eye, after its own zoom collision (Minecraft blocks and the host's triangles).",
     "// the eye, after its own zoom collision (Minecraft blocks and the host's triangles)."),
    ("// posed and animated, with positions in blocks relative to the player's feet: the host puts",
     "// posed and animated, with positions in blocks relative to the player's feet: the host puts"),
    ("// the host hangs the parts on its ragdoll when the player dies (SA: CreateRagdoll)",
     "// the host hangs the parts on its ragdoll when the player dies (SA: CreateRagdoll)"),
    ("// Reader (the host) does xchg(state, front) only when", "// Reader (the host) does xchg(state, front) only when"),
    ("// ---- input ring @0x1000 (host produces, MC consumes)", "// ---- input ring @0x1000 (host produces, MC consumes)"),
    ("// ---- event ring @0x17000 (MC -> host)", "// ---- event ring @0x17000 (MC -> host)"),
    ("// ---- world entities @0x1C000 (MC -> host, seqlock)", "// ---- world entities @0x1C000 (MC -> host, seqlock)"),
    ("// Minecraft things the host draws itself each frame", "// Minecraft things the host draws itself each frame"),
    ("// ---- host -> MC state @0x100", "// ---- host -> MC state @0x100"),
    ("// ---- MC -> host state @0x200", "// ---- MC -> host state @0x200"),
    ("// ---- collision ring @0x20000 (host produces, MC consumes)", "// ---- collision ring @0x20000 (host produces, MC consumes)"),
    ("// ---- actor table @0x12000 (host -> MC, seqlock)", "// ---- actor table @0x12000 (host -> MC, seqlock)"),
    ("// ---- water grid", "// ---- water grid"),
    ("kSkyInGame = 1u << 0,    // the host has a loaded world and a live player",
     "kSkyInGame = 1u << 0,    // the host has a loaded world and a live player"),
    ("kSkyMenuOpen = 1u << 1,  // a host menu owns input (SA: pause/MISSION); MC should drop held keys",
     "kSkyMenuOpen = 1u << 1,  // a host menu owns input (SA: pause/MISSION); MC should drop held keys"),
    ("kSkyLoading = 1u << 2,   // loading screen / area transition in progress",
     "kSkyLoading = 1u << 2,   // loading screen / area transition in progress"),
    ("kEvHitActor = 1,    // entityIndex (SA: entity index), a = MC damage (after MC's own modifiers),
                    // b/c = knockback dir x/z (MC), d = knockback strength",
     "kEvHitActor = 1,    // entityIndex (SA: entity index), a = MC damage (after MC's own modifiers),\n"
     "                    // b/c = knockback dir x/z (MC), d = knockback strength"),
    ("kEvPlayerDied = 2,  // the Minecraft player died: kill the host player",
     "kEvPlayerDied = 2,  // the Minecraft player died: kill the host player"),
    ("kEvExplosion = 3,   // a Minecraft explosion (TNT, creeper, ...): a/b/c = centre (MC coords),
                    // d = radius (blocks). The host applies SA-radius damage and blows car doors.",
     "kEvExplosion = 3,   // a Minecraft explosion (TNT, creeper, ...): a/b/c = centre (MC coords),\n"
     "                    // d = radius (blocks). The host applies SA-radius damage and blows car doors."),
    ("kEvArrowStuck = 4,  // an arrow stuck in a host actor", "kEvArrowStuck = 4,  // an arrow stuck in a host actor"),
    ("// What landed a kEvHitActor (the host plays that weapon class's impact effect and sounds).",
     "// What landed a kEvHitActor (the host plays that weapon class's impact effect and sounds)."),
    ("kWeaponPierce = 4,  // tridents, spears (SA: mapped to the knife slot)", "kWeaponPierce = 4,  // tridents, spears (SA: mapped to the knife slot) (SA: mapped to the knife slot)"),
]

# Blind word swaps, applied after LITERAL.  Order matters: phrases before words.
WORD: list[tuple[str, str]] = [
    ("GTA San Andreas", "GTA San Andreas"),
    ("the opening mission", "the opening mission"),
    ("SA", "SA"),
    ("sa", "sa"),
    ("SA-host", "SA-host"),
    ("Sa", "Sa"),
    ("San Andreas", "San Andreas"),
    ("Los Santos", "Los Santos"),
    ("Idlewood", "Idlewood"),
    ("the Joyboy tutorial", "the Joyboy tutorial"),
    ("BulletAI", "BulletAI"),
    ("bulletai", "bulletai"),
    ("entity index", "entity index"),
    ("entityIndex", "entityIndex"),
    ("entityIndexs", "entityIndexes"),
    ("mod sites", "mod sites"),
]

# Whole lines to drop: they only make sense for the SA half.
DROP_LINE_PREFIXES = [
    "| [Address Library for SA-host Plugins]",
    "| [SA-host64]",
]


def rewrite(text: str) -> str:
    for old, new in LITERAL:
        if old in text:
            text = text.replace(old, new)
    for old, new in WORD:
        if old in text:
            text = text.replace(old, new)
    lines = [l for l in text.split("\n") if not any(l.strip().startswith(p) for p in DROP_LINE_PREFIXES)]
    return "\n".join(lines)


# --------------------------------------------------------------------------------------

def files() -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file():
            rel = path.relative_to(ROOT)
            if in_scope(rel):
                out.append(path)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="print what would change; write nothing")
    args = ap.parse_args()

    changed = 0
    for path in files():
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        updated = rewrite(original)
        if updated != original:
            changed += 1
            if not args.check:
                path.write_text(updated, encoding="utf-8")
            print(f"port: {path.relative_to(ROOT)}")

    pattern = re.compile(r"sa|skse|tamriel|whiterun|formid", re.IGNORECASE)
    leftovers = []
    for path in files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                leftovers.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()[:120]}")

    print(f"\n{changed} files rewritten")
    if leftovers:
        print(f"{len(leftovers)} lines still mention the old game:")
        for l in leftovers:
            print("  " + l)
    else:
        print("clean: no SA references left in scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
