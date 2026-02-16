extends Node2D

@onready var world_view: Node2D = $WorldView
@onready var ui_layer: Control = $CanvasLayer/GameUI

var selected_room_type: String = "Living"

func _ready() -> void:
	BaseManager.room_built.connect(_refresh_world)
	BaseManager.tile_dug.connect(_refresh_world)
	SurfaceSimulation.day_advanced.connect(_on_day_advanced)
	EventSystem.log_event.connect(_on_log_event)
	ui_layer.room_selected.connect(_on_room_selected)
	ui_layer.dig_requested.connect(_on_dig_requested)
	ui_layer.build_requested.connect(_on_build_requested)
	ui_layer.mission_requested.connect(_on_mission_requested)
	_refresh_world(Vector2i.ZERO)
	ui_layer.update_day_and_weather(SurfaceSimulation.day_index, SurfaceSimulation.current_weather)

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var tile := world_view.screen_to_grid(event.position)
		if tile.y >= 0:
			BaseManager.dig_tile(tile)
			BaseManager.build_room(tile, selected_room_type)

func _on_room_selected(room_type: String) -> void:
	selected_room_type = room_type

func _on_dig_requested(grid_pos: Vector2i) -> void:
	BaseManager.dig_tile(grid_pos)

func _on_build_requested(grid_pos: Vector2i, room_type: String) -> void:
	BaseManager.build_room(grid_pos, room_type)

func _on_mission_requested(survivor_id: int, mission_type: String) -> void:
	SurvivorManager.send_to_surface_mission(survivor_id, mission_type)

func _on_day_advanced(day_index: int) -> void:
	ui_layer.update_day_and_weather(day_index, SurfaceSimulation.current_weather)

func _on_log_event(message: String) -> void:
	ui_layer.push_log_line(message)

func _refresh_world(_arg) -> void:
	world_view.queue_redraw()
