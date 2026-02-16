extends Node

## Central event bus that decouples gameplay systems.
signal log_event(message: String)

func _ready() -> void:
	SurfaceSimulation.surface_event_triggered.connect(_on_surface_event)
	SurvivorManager.mission_finished.connect(_on_mission_finished)
	BaseManager.room_under_attack.connect(_on_room_under_attack)

func _on_surface_event(event_type: String, payload: Dictionary) -> void:
	match event_type:
		"EnemyWave":
			log_event.emit("Enemy wave incoming (power %d) at %s." % [payload["strength"], payload["entry"]])
		"ResourceDrop":
			log_event.emit("Resource crate spotted on surface: +%d scrap." % payload["scrap"])
		"TravelerSignal":
			log_event.emit("Distress signal detected. Potential reward: %s." % payload["reward"])

func _on_mission_finished(survivor_id: int, mission_type: String, success: bool, reward: Dictionary) -> void:
	var result := success ? "success" : "failure"
	log_event.emit("Mission '%s' ended with %s. Loot: %s" % [mission_type, result, str(reward)])

func _on_room_under_attack(grid_pos: Vector2i, remaining_hp: int) -> void:
	log_event.emit("Room at %s was hit! HP left: %d" % [str(grid_pos), remaining_hp])
