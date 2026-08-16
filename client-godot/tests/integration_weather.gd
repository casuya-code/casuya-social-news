extends SceneTree
## Headless integration test for in-client weather sync (Features #14/#30).
## - NetworkManager.fetch_weather() -> weather_loaded payload (live server)
## - WeatherWidget maps the payload to a Swahili status line (condition,
##   time of day, mood bias), including the offline/unknown fallback.

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")
const WIDGET_SCRIPT := preload("res://ui/WeatherWidget.gd")
const OCCLUSION_SCRIPT := preload("res://audio/AcousticOcclusion.gd")

var _network: Node
var _widget: Label
var _occlusion: Node
var _player: AudioStreamPlayer3D
var _passed := false
var _payload: Dictionary = {}


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame

	# --- AcousticOcclusion weather bias (Feature #30 audio reaction) ---
	_occlusion = OCCLUSION_SCRIPT.new()
	root.add_child(_occlusion)
	_player = AudioStreamPlayer3D.new()
	root.add_child(_player)
	_occlusion.apply_to(_player, "char_mjomba", "anapiga_kelele")
	var base_db: float = _player.volume_db
	_occlusion.set_weather_bias(-1.0)
	_occlusion.apply_to(_player, "char_mjomba", "anapiga_kelele")
	if not (_player.volume_db < base_db):
		_fail("stormy weather should darken audio: base=%f stormy=%f" % [base_db, _player.volume_db])
		return
	var stormy_db: float = _player.volume_db
	_occlusion.set_weather_bias(1.0)
	_occlusion.apply_to(_player, "char_mjomba", "anapiga_kelele")
	if not (_player.volume_db > stormy_db):
		_fail("bright weather should lift audio: stormy=%f bright=%f" % [stormy_db, _player.volume_db])
		return
	# Clamped to [-1, 1].
	_occlusion.set_weather_bias(5.0)
	if _occlusion.weather_bias() != 1.0:
		_fail("weather bias should clamp at 1.0")
		return
	print("[TEST] occlusion weather bias: base=%f stormy=%f bright=%f" % [base_db, stormy_db, _player.volume_db])
	_occlusion.queue_free()
	_player.queue_free()

	# --- WeatherWidget pure mapping (no server needed) ---
	_widget = WIDGET_SCRIPT.new()
	root.add_child(_widget)
	_widget.show_weather({"condition": "dhoruba", "time_of_day": "usiku", "mood_offset": -0.4, "location": "Dar es Salaam"})
	if not _widget.text.contains("Dhoruba"):
		_fail("widget did not map dhoruba condition: %s" % _widget.text)
		return
	if not _widget.text.contains("Usiku"):
		_fail("widget did not map time-of-day: %s" % _widget.text)
		return
	if not _widget.text.contains("chini"):
		_fail("widget did not describe low mood: %s" % _widget.text)
		return

	_widget.show_weather({"condition": "angavu", "time_of_day": "asubuhi", "mood_offset": 0.2, "location": "Nairobi"})
	if not _widget.text.contains("Angavu") or not _widget.text.contains("Asubuhi"):
		_fail("widget failed on clear/morning: %s" % _widget.text)
		return
	if not _widget.text.contains("juu"):
		_fail("widget did not describe lifted mood: %s" % _widget.text)
		return

	_widget.show_unknown()
	if _widget.text != "":
		_fail("show_unknown should blank the label")
		return

	_widget.queue_free()

	# --- live: fetch /weather ---
	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "test-key"
	_network.base_url = "http://127.0.0.1:8000"
	_network.weather_loaded.connect(_on_weather_loaded)
	_network.api_error.connect(_on_api_error)
	await process_frame
	_network.fetch_weather()
	create_timer(20.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — no weather_loaded received")
			quit(1)
	)


func _on_weather_loaded(payload: Dictionary) -> void:
	_payload = payload
	if not payload.has("condition"):
		_fail("weather payload missing condition: %s" % str(payload))
		return
	if not payload.has("time_of_day"):
		_fail("weather payload missing time_of_day")
		return
	if not payload.has("mood_offset"):
		_fail("weather payload missing mood_offset")
		return
	print("[TEST] PASS — widget mapping + occlusion bias + live weather=%s period=%s mood=%s" % [
		payload.get("condition", ""),
		payload.get("time_of_day", ""),
		payload.get("mood_offset", ""),
	])
	_passed = true
	quit(0)


func _on_api_error(error_code: String, message: String) -> void:
	_fail("weather fetch errored: %s (%s)" % [error_code, message])


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)