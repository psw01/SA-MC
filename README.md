# SACraft

![SACraft: a Minecraft player walking through Idlewood with the Minecraft HUD](docs/screenshot.jpg)

Play SA as a Minecraft player. You move with Minecraft's physics, carry Minecraft's inventory
and HUD, and place and break blocks in SA's world. You fight SA's NPCs with Minecraft
weapons, and they fight back.

Neither game is rewritten. Minecraft runs its own game logic, and SA runs its world, NPCs,
quests and saves. A SA SA-host plugin and a Minecraft Fabric mod talk to each other through
shared memory. Minecraft runs hidden in the background, and SA draws everything.

> **Status: early and experimental.** Expect rough edges, and back up your saves.
> This is a fan project. It isn't affiliated with Mojang, Microsoft, Bethesda or ZeniMax, and you
> need to own both games.

## What works

- **Movement:** Minecraft movement on SA's terrain and buildings. That covers walking,
  sprinting, jumping, crouching, swimming and falling, and SA's collision is fed into
  Minecraft's own collision.
- **Blocks:** place and break blocks anywhere in SA. They're drawn inside SA's frame
  with its sun, shadows, fog and weather. Minecraft lights (torches, lava, glowstone and so on)
  light up SA.
- **Digging into SA:** mine SA's ground, rocks, roads and objects like Minecraft blocks.
  What you dig out drops as the block it's made of (dirt under grass, then stone with ores, then
  bedrock), and the hole is real for you, NPCs and items. TNT, creepers and other explosions blow
  craters into SA. Interiors and caves are solid stone behind their walls. What you dig is
  saved in your Minecraft world. **SA destruction: On/Off** in the top left of the pause menu
  (O) turns it off (holes already dug stay).
- **Block entities:** chests, beds, banners, heads, shulker boxes and similar blocks are drawn,
  and pistons move blocks.
- **Water and lava:** they flow over SA's terrain, and SA water swims like Minecraft
  water.
- **Combat:** hit SA NPCs with any Minecraft weapon, including bows, tridents and TNT.
  Damage is scaled to NPC level, and NPCs fight back.
  - NPCs collide with blocks and path around them.
  - Lava and fire hurt NPCs, and NPCs press pressure plates.
- **SA progression:**
  - Your SA skills level up from Minecraft play. Swords, maces and tools train
    One-Handed; axes and spears train Two-Handed; bows and anything thrown train Archery.
  - Shields train Block, and hits taken train Light or Heavy Armor depending on what you wear.
  - Crafting gear trains Smithing, and crouching is SA sneak, which trains Sneak.
- **Camera and death:** Minecraft's F5 camera modes show your skin and armor in SA. Dying
  gives SA's death camera with your Minecraft body ragdolling.
- **SA's own animations:** chairs, crafting stations, beds, pull levers, horses and scripted
  scenes hand control to SA until they finish.
- **Multiplayer (Minecraft side only):** friends who also run SACraft can join your Minecraft
  world over the internet (see [Playing with friends](#playing-with-friends)).

## Requirements

**SA**

| | |
|---|---|
| GTA San Andreas, **Anniversary Edition runtime** (1.6.x / 1.7.x) | Developed and tested on **1.7.104**. Not SE 1.5.97, not VR. |
| [SA-host64](https://skse.silverlock.org/) | For your game version |
| [Address Library for SA-host Plugins](https://www.nexusmods.com/saspecialedition/mods/32444) | The "All in one (Anniversary Edition)" file |

> **Heavily recommended: [Alternate Start - Live Another Life](https://www.nexusmods.com/saspecialedition/mods/272).**
> the opening mission (the cart ride and the Joyboy tutorial) is heavily scripted and may not work with SACraft,
> so you can get stuck. Alternate Start skips it and lets you choose where your new character
> begins. Otherwise, play from a save made after the Joyboy tutorial.

**Minecraft**

You only need **a Microsoft account that owns Minecraft: Java Edition**. SACraft comes with
everything else: a portable [Prism Launcher](https://prismlauncher.org/) set up with Minecraft 26.3,
[Fabric](https://fabricmc.net/), [Fabric API](https://modrinth.com/mod/fabric-api) and the SACraft
Minecraft mod. Prism downloads Minecraft and Java itself.

Minecraft runs hidden next to SA. Budget about 3 GB of extra RAM, about 1.5 GB of disk for
Minecraft's own files, and a GPU that runs Minecraft 26.3.

## Installing

1. **Install `SACraft-<version>.zip`** with Mod Organizer 2 or Vortex, like any SA-host plugin.
2. **Start SA through SA-host.** The first time, SACraft unpacks its Minecraft to
   `%LOCALAPPDATA%\SACraft` and a small **Prism Launcher** window asks you to sign in with your
   Microsoft account. Alt-Tab to it, sign in, then go back to SA. Prism downloads Minecraft,
   Fabric and Java (a few minutes, first time only), and SA's corner messages tell you when
   Minecraft is ready.
3. **After that it's automatic.** Minecraft starts with SA with no window and no sound, opens
   its SACraft world by itself (a new Survival world, created on your PC), and quits when SA
   closes.

Updating: install the new SACraft zip over the old one. The next start updates the Minecraft side
too and keeps your sign-in and your world.

Uninstalling: remove the mod, then delete `%LOCALAPPDATA%\SACraft`. That folder holds Prism, your
Microsoft sign-in (Prism's), Minecraft's files and your SACraft world.

### Using your own launcher

`Data/SA-host/Plugins/SACraft.ini` can point SACraft at your own Prism, MultiMC or `.bat` file instead:

```ini
[Minecraft]
bStartWithSA = 1              ; 0: start Minecraft yourself, any way you like
sLauncher =                       ; empty: the Minecraft that comes with SACraft
sArguments = --launch SACraft    ; what your launcher needs to start the SACraft instance
```

Your instance needs Minecraft 26.3, Fabric Loader 0.19.5 or newer, Fabric API, Java 25 and
`sacraft-fabric-<version>.jar` (from the release), plus `-Dsacraft.startHidden=true` in its
JVM arguments if it should stay hidden from the start. SACraft never starts a second Minecraft if
one with the mod is already running. It starts Minecraft through Windows' shell, so under Mod
Organizer Minecraft stays outside MO2's virtual file system and doesn't keep MO2 locked.

## Playing with friends

Everyone needs their own SA with SACraft. Only the Minecraft world is shared: blocks, items,
mobs and each other. Up to 100 players. Each player keeps their own SA world, NPCs and quests.

1. **Host:** press **O** (Minecraft's menu), choose **Open to LAN**, then **Start LAN World**.
   SACraft's bundled [e4mc](https://modrinth.com/mod/e4mc) puts a link like `abc-def.e4mc.link`
   in chat. Click it to copy it, then send it to your friends.
2. **Friends:** press **T** and type `/join abc-def.e4mc.link`. Your Minecraft leaves its own
   world and joins the host's.
3. **`/leave`** goes back to your own world. If the host closes their world, you're put back in
   yours automatically.

**With Discord:** your Discord status shows SACraft while you play. Once you've opened your world
to LAN it has a **Join** button (and you can invite friends from a Discord chat). A friend with
SA and SACraft already running clicks it and joins you, no link needed.

## Controls

Minecraft has priority. These keys still go to SA:

| Key | Does |
|---|---|
| **G** | SA activate: doors, NPCs (talk), containers, levers, furniture |
| **Esc** | SA menu (or closes an open Minecraft screen) |
| **J** / **M** | SA journal / map |
| **H** | SA wait |
| **F9** | SA quickload (save from the Esc menu) |
| **~** | SA console |
| **O** | Minecraft pause / options menu |

Every other key is Minecraft's: **E** inventory, **F5** camera, **T** chat, **/** commands,
**Shift** crouch/sneak, and so on.

## Known limitations

- If something goes wrong, `Documents\My Games\GTA San Andreas\SA-host\SACraft.log` says what.
  For bug reports, set `bDiagnostics = 1` in `SACraft.ini` for detailed logs.
- **Stuck on "SACraft: starting Minecraft..."?** After a minute SACraft says which of these it is:
  - Prism Launcher is still busy. Alt-Tab to it: it may be downloading, or need you to sign in,
    or show an error.
  - Minecraft closed. Its log is
    `%LOCALAPPDATA%\SACraft\Prism\instances\SACraft\.minecraft\logs\latest.log`.
  - Minecraft is running but not responding. Please report it, with `SACraft.log` and that
    `latest.log`.

  You need to own Minecraft: Java Edition.

- the opening mission (cart ride and the Joyboy tutorial) may leave you stuck. Use
  [Alternate Start](https://www.nexusmods.com/saspecialedition/mods/272) or a save made after the Joyboy tutorial.
- SA's inventory, magic, shouts and perks can't be opened while Minecraft drives the player.
- Minecraft hits only reach NPCs, not SA objects such as the web around Arvel in Bleak Falls
  Barrow. There's no in-game switch back to plain SA yet. Closing Minecraft hands control
  back to SA; Minecraft keeps what it last autosaved, every few minutes. Deal with the object,
  then restart SA to bring Minecraft back.
- Sign text isn't drawn yet.
- All SA interiors share one Minecraft world, so blocks placed in one interior can appear in
  another at the same coordinates.
- Multiplayer syncs only the Minecraft world. Each player has their own SA, and guests
  can't hit their own SA NPCs yet.
- Mods that also take over the camera (Improved Camera SE, SmoothCam, True Directional Movement)
  will conflict.

## Building from source

You need Visual Studio 2026 (C++), CMake 3.25+, Git, and JDK 25.

```bat
git clone --recursive <this repo> sacraft
cd sacraft
git clone https://github.com/microsoft/vcpkg .tools\vcpkg
.tools\vcpkg\bootstrap-vcpkg.bat

cd skse
cmake --preset default
cmake --build --preset release

cd ..\fabric
gradlew build

cd ..
powershell -ExecutionPolicy Bypass -File tools\package.ps1 -NoBuild
```

`tools\package.ps1` builds both halves (drop `-NoBuild`) and writes the release files to `dist\`.

For development:

- `fabric\gradlew runClient` starts a dev Minecraft that stays running when SA closes.
- With `SACRAFT_DEPLOY_DIR` (preset default: the MO2 mod folder `mods\SACraft`, if it exists),
  each plugin build is copied straight into Mod Organizer.
- `docs\DESIGN.md` explains how the two halves fit together, and `protocol\skycraft_protocol.h`
  is the shared-memory layout both sides follow.

| Folder | |
|---|---|
| `skse/` | The SA SA-host plugin (C++, [CommonLibSSE-NG](https://github.com/alandtse/CommonLibVR/tree/ng)) |
| `fabric/` | The Minecraft Fabric mod (Java) |
| `protocol/` | The shared-memory protocol between them |
| `tools/` | Packaging, test stand-ins (`fake_sa.py`, `fake_guest.py`) and diagnostics |

## License

[MIT](LICENSE)
