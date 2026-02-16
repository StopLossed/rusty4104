# Cross-Section Survival Prototype (Godot)

Fast, extensible prototype for a **casual survival/base-building game** inspired by the ad-style fantasy of bunker + surface management.

## Prototype features

- **Always-visible vertical cross-section**: ruined city surface + underground bunker in one camera view.
- **Underground base loop**:
  - Dig new tiles.
  - Build room types (Living, Power, Food, Storage, Research, Defense, Turret, Trap).
  - Assign survivors to improve room efficiency.
- **Surface simulation loop**:
  - Advancing days, changing weather.
  - Dynamic events (enemy waves, resource drops, traveler signals).
  - Send survivors on scavenging missions.
- **Defense foundations**:
  - Rooms have HP and defense stats.
  - Event bus supports enemy pressure and room damage messaging.
- **Progression scaffolding**:
  - Threat level increases over time.
  - Survivor traits/stats support rare specialist expansion.

## Engine

- Built with **Godot 4.x** using GDScript.

## Project structure

```text
godot/
├── project.godot
├── scenes/
│   └── Main.tscn
└── scripts/
    ├── main.gd
    ├── data/
    │   └── room_data.gd
    ├── systems/
    │   ├── base_manager.gd
    │   ├── event_system.gd
    │   ├── surface_simulation.gd
    │   └── survivor_manager.gd
    └── ui/
        ├── game_ui.gd
        └── world_view.gd
```

## Architecture (modular + scalable)

- `BaseManager` (autoload): bunker digging/building/room state.
- `SurfaceSimulation` (autoload): day ticks, weather, threat, surface events.
- `SurvivorManager` (autoload): roster/stats, assignment bonuses, mission handling.
- `EventSystem` (autoload): event bus to decouple systems from UI and gameplay controller.
- `Main` scene controller: routes input and updates world/UI.

This separation is meant to make future replacement easy (e.g., swap procedural events, add tech tree, move mission logic to data-driven configs).

## Example level included

On boot, the game seeds a small starter bunker:

- Dug tunnel segment underground.
- Rooms already placed: Living, Power, Food, Storage.
- Starter survivor roster with varied stats.

## Controls (prototype)

- **Left click underground**: dig tile and build currently selected room type.
- **Room selector (UI panel)**: choose build type.
- **Select survivor + "Send Scavenge Mission"**: trigger a surface mission.

## How to run

1. Open Godot 4.x.
2. Import project from `godot/project.godot`.
3. Run `Main.tscn` (or just press Play since it is the main scene).

## Notes for extension

- Add tech unlocks by introducing a `TechManager` and gating `BaseManager.ROOM_LIBRARY` entries.
- Add enemy entities by connecting `SurfaceSimulation.surface_event_triggered` to spawn controllers.
- Add drag-and-drop placement by replacing click handler in `scripts/main.gd` with ghost preview + confirm interaction.
