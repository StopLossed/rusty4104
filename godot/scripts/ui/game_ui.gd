extends Control

signal room_selected(room_type: String)
signal dig_requested(grid_pos: Vector2i)
signal build_requested(grid_pos: Vector2i, room_type: String)
signal mission_requested(survivor_id: int, mission_type: String)

@onready var room_option: OptionButton = $Panel/RoomOption
@onready var day_label: Label = $Panel/DayLabel
@onready var weather_label: Label = $Panel/WeatherLabel
@onready var log_box: RichTextLabel = $Panel/Log
@onready var survivors_list: ItemList = $Panel/Survivors

func _ready() -> void:
	for room_name in BaseManager.ROOM_LIBRARY.keys():
		room_option.add_item(room_name)
	room_option.item_selected.connect(_on_room_option_selected)
	$Panel/SendMissionButton.pressed.connect(_on_send_mission_pressed)
	_refresh_survivors()

func update_day_and_weather(day_index: int, weather_name: String) -> void:
	day_label.text = "Day %d" % day_index
	weather_label.text = "Weather: %s" % weather_name

func push_log_line(message: String) -> void:
	log_box.append_text("• %s\n" % message)

func _refresh_survivors() -> void:
	survivors_list.clear()
	for id in SurvivorManager.survivors.keys():
		var s: Dictionary = SurvivorManager.survivors[id]
		survivors_list.add_item("%s  [STR %d / INT %d / STA %d]" % [s["name"], s["strength"], s["intelligence"], s["stamina"]])
		survivors_list.set_item_metadata(survivors_list.item_count - 1, id)

func _on_room_option_selected(index: int) -> void:
	room_selected.emit(room_option.get_item_text(index))

func _on_send_mission_pressed() -> void:
	if survivors_list.get_selected_items().is_empty():
		push_log_line("Select a survivor first.")
		return
	var selected_idx := survivors_list.get_selected_items()[0]
	var survivor_id: int = survivors_list.get_item_metadata(selected_idx)
	mission_requested.emit(survivor_id, "Scavenge")
	push_log_line("Sent %s on a Scavenge mission." % SurvivorManager.survivors[survivor_id]["name"])
