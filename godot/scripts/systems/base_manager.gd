extends Node

## Base-management system responsible for bunker tiles, construction, and defenses.
signal room_built(grid_pos: Vector2i, room_type: String)
signal tile_dug(grid_pos: Vector2i)
signal room_under_attack(grid_pos: Vector2i, remaining_hp: int)

const GRID_WIDTH: int = 14
const GRID_HEIGHT: int = 10
const ROOM_LIBRARY := {
	"Living": {"hp": 120, "defense": 1, "tag": "housing"},
	"Power": {"hp": 100, "defense": 1, "tag": "energy"},
	"Food": {"hp": 100, "defense": 1, "tag": "food"},
	"Storage": {"hp": 130, "defense": 2, "tag": "storage"},
	"Research": {"hp": 90, "defense": 1, "tag": "science"},
	"Defense": {"hp": 150, "defense": 4, "tag": "defense"},
	"Turret": {"hp": 140, "defense": 5, "tag": "defense"},
	"Trap": {"hp": 80, "defense": 3, "tag": "defense"}
}

var dug_tiles: Dictionary = {}
var rooms: Dictionary = {}

func _ready() -> void:
	_seed_example_layout()

func _seed_example_layout() -> void:
	# Example level chunk used as a quick prototype start.
	for x in range(4, 10):
		dig_tile(Vector2i(x, 0))
	build_room(Vector2i(5, 0), "Living")
	build_room(Vector2i(6, 0), "Power")
	build_room(Vector2i(7, 0), "Food")
	build_room(Vector2i(8, 0), "Storage")

func dig_tile(grid_pos: Vector2i) -> bool:
	if not _is_valid_tile(grid_pos):
		return false
	dug_tiles[grid_pos] = true
	tile_dug.emit(grid_pos)
	return true

func build_room(grid_pos: Vector2i, room_type: String) -> bool:
	if not dug_tiles.has(grid_pos):
		return false
	if not ROOM_LIBRARY.has(room_type):
		return false

	var base_stats: Dictionary = ROOM_LIBRARY[room_type]
	var room := {
		"type": room_type,
		"hp": base_stats["hp"],
		"max_hp": base_stats["hp"],
		"defense": base_stats["defense"],
		"production_tag": base_stats["tag"],
		"assigned": []
	}
	rooms[grid_pos] = room
	room_built.emit(grid_pos, room_type)
	return true

func assign_survivor_to_room(grid_pos: Vector2i, survivor_id: int) -> bool:
	if not rooms.has(grid_pos):
		return false
	var assigned: Array = rooms[grid_pos]["assigned"]
	if survivor_id in assigned:
		return false
	assigned.append(survivor_id)
	rooms[grid_pos]["assigned"] = assigned
	return true

func apply_attack_damage(grid_pos: Vector2i, incoming_damage: int) -> void:
	if not rooms.has(grid_pos):
		return
	var room: Dictionary = rooms[grid_pos]
	var mitigated: int = maxi(1, incoming_damage - int(room["defense"]))
	room["hp"] = maxi(0, int(room["hp"]) - mitigated)
	rooms[grid_pos] = room
	room_under_attack.emit(grid_pos, room["hp"])
	if room["hp"] == 0:
		rooms.erase(grid_pos)

func get_room_efficiency(grid_pos: Vector2i) -> float:
	if not rooms.has(grid_pos):
		return 0.0
	var room: Dictionary = rooms[grid_pos]
	var total_bonus := 1.0
	for survivor_id in room["assigned"]:
		total_bonus += SurvivorManager.get_assignment_bonus(survivor_id, String(room["production_tag"]))
	return total_bonus

func _is_valid_tile(grid_pos: Vector2i) -> bool:
	return grid_pos.x >= 0 and grid_pos.x < GRID_WIDTH and grid_pos.y >= 0 and grid_pos.y < GRID_HEIGHT
