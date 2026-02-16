extends Node

## Handles survivor roster, assignment logic, and surface missions.
signal mission_started(survivor_id: int, mission_type: String)
signal mission_finished(survivor_id: int, mission_type: String, success: bool, reward: Dictionary)

var survivors: Dictionary = {}
var next_survivor_id: int = 1

func _ready() -> void:
	_spawn_example_survivors()

func _spawn_example_survivors() -> void:
	create_survivor("Ari", 6, 4, 5)
	create_survivor("Milo", 3, 7, 4)
	create_survivor("Rin", 5, 5, 8, "Medic")

func create_survivor(name: String, strength: int, intelligence: int, stamina: int, trait: String = "") -> int:
	var id := next_survivor_id
	next_survivor_id += 1
	survivors[id] = {
		"id": id,
		"name": name,
		"strength": strength,
		"intelligence": intelligence,
		"stamina": stamina,
		"trait": trait,
		"state": "Idle"
	}
	return id

func get_assignment_bonus(survivor_id: int, production_tag: String) -> float:
	if not survivors.has(survivor_id):
		return 0.0
	var s: Dictionary = survivors[survivor_id]
	match production_tag:
		"energy":
			return float(s["intelligence"]) * 0.03
		"food":
			return float(s["stamina"]) * 0.03
		"science":
			return float(s["intelligence"]) * 0.05
		"defense":
			return float(s["strength"]) * 0.04
		_:
			return 0.02

func send_to_surface_mission(survivor_id: int, mission_type: String) -> void:
	if not survivors.has(survivor_id):
		return
	survivors[survivor_id]["state"] = "Mission"
	mission_started.emit(survivor_id, mission_type)
	# Prototype async mission result with a short timer.
	await get_tree().create_timer(2.0).timeout
	var success_chance := 0.5 + float(survivors[survivor_id]["stamina"]) * 0.04
	var success := randf() <= clampf(success_chance, 0.2, 0.95)
	var reward := {
		"scrap": randi_range(10, 30),
		"food": randi_range(4, 15),
		"research": success ? randi_range(0, 8) : 0
	}
	survivors[survivor_id]["state"] = "Idle"
	mission_finished.emit(survivor_id, mission_type, success, reward)
