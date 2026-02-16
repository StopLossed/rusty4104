extends Resource
class_name RoomData

## Lightweight data container used by BaseManager for every room tile.
@export var room_type: String = "Empty"
@export var hit_points: int = 100
@export var defense_rating: int = 0
@export var production_tag: String = ""
@export var size: Vector2i = Vector2i.ONE

func _init(p_type: String = "Empty", p_hp: int = 100, p_defense: int = 0, p_tag: String = "") -> void:
	room_type = p_type
	hit_points = p_hp
	defense_rating = p_defense
	production_tag = p_tag
