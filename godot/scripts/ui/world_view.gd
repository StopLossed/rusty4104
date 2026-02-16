extends Node2D

## Draws the shared surface + underground cross-section view.
const TILE_SIZE: int = 48
const SURFACE_Y: int = 220

const ROOM_COLORS := {
	"Living": Color("#8ad0ff"),
	"Power": Color("#f7d354"),
	"Food": Color("#7be072"),
	"Storage": Color("#ba9efc"),
	"Research": Color("#fca7cc"),
	"Defense": Color("#ff9a76"),
	"Turret": Color("#ff7e5f"),
	"Trap": Color("#e9724c")
}

func _draw() -> void:
	_draw_surface()
	_draw_underground()

func _draw_surface() -> void:
	draw_rect(Rect2(0, 0, 1280, SURFACE_Y), Color("#5d768f"), true)
	draw_rect(Rect2(0, SURFACE_Y - 24, 1280, 24), Color("#3d4e5d"), true)
	# Stylized skyline ruins.
	for i in range(10):
		var x := 40 + i * 120
		draw_rect(Rect2(x, SURFACE_Y - 120 - (i % 3) * 25, 70, 110), Color("#2f3943"), true)
	# Weather tint.
	if SurfaceSimulation.current_weather == "Storm":
		draw_rect(Rect2(0, 0, 1280, SURFACE_Y), Color(0.3, 0.3, 0.35, 0.2), true)
	elif SurfaceSimulation.current_weather == "Radiation Burst":
		draw_rect(Rect2(0, 0, 1280, SURFACE_Y), Color(0.1, 0.8, 0.3, 0.18), true)

func _draw_underground() -> void:
	draw_rect(Rect2(0, SURFACE_Y, 1280, 500), Color("#4f3f33"), true)
	for tile in BaseManager.dug_tiles.keys():
		var rect := _tile_rect(tile)
		draw_rect(rect, Color("#7b624f"), true)
		draw_rect(rect, Color("#2d221a"), false, 2.0)
	for pos in BaseManager.rooms.keys():
		var room: Dictionary = BaseManager.rooms[pos]
		var rrect := _tile_rect(pos)
		var room_color: Color = ROOM_COLORS.get(room["type"], Color.WHITE)
		draw_rect(rrect.grow(-2), room_color, true)
		var hp_ratio := float(room["hp"]) / float(room["max_hp"])
		draw_rect(Rect2(rrect.position + Vector2(4, 4), Vector2((TILE_SIZE - 8) * hp_ratio, 6)), Color("#3ee05d"), true)

func _tile_rect(grid_pos: Vector2i) -> Rect2:
	var base := Vector2(220, SURFACE_Y + 30)
	var p := base + Vector2(grid_pos.x * TILE_SIZE, grid_pos.y * TILE_SIZE)
	return Rect2(p, Vector2(TILE_SIZE, TILE_SIZE))

func screen_to_grid(screen_pos: Vector2) -> Vector2i:
	var local := screen_pos - Vector2(220, SURFACE_Y + 30)
	return Vector2i(floori(local.x / TILE_SIZE), floori(local.y / TILE_SIZE))
