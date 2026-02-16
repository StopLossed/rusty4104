extends Node

## Simulates dangerous surface states: weather, waves, and drops.
signal day_advanced(day_index: int)
signal surface_event_triggered(event_type: String, payload: Dictionary)

var day_index: int = 1
var threat_level: float = 1.0
var current_weather: String = "Clear"

func _ready() -> void:
	start_tick_loop()

func start_tick_loop() -> void:
	while true:
		await get_tree().create_timer(5.0).timeout
		_simulate_day_tick()

func _simulate_day_tick() -> void:
	day_index += 1
	threat_level += 0.15
	current_weather = _roll_weather()
	day_advanced.emit(day_index)
	_try_trigger_surface_event()

func _roll_weather() -> String:
	var roll := randf()
	if roll < 0.55:
		return "Dusty"
	if roll < 0.75:
		return "Storm"
	if roll < 0.92:
		return "Toxic Rain"
	return "Radiation Burst"

func _try_trigger_surface_event() -> void:
	var roll := randf()
	if roll < 0.38:
		surface_event_triggered.emit("EnemyWave", {
			"strength": int(5 * threat_level),
			"entry": "Main Gate"
		})
	elif roll < 0.7:
		surface_event_triggered.emit("ResourceDrop", {
			"scrap": randi_range(20, 50),
			"coordinates": Vector2(randi_range(80, 1200), 140)
		})
	else:
		surface_event_triggered.emit("TravelerSignal", {
			"difficulty": randi_range(1, 3),
			"reward": "Rare Survivor"
		})
