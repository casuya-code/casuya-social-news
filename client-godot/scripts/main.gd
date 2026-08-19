extends Control
## Main scene — fetches endless stories and plays them with dialogue UI.
##
## Flow:
##   1. Press "Anza" (Start) -> Network.refresh_news()
##   2. news_loaded(scripts) -> pick first script, Network.generate_audio()
##   3. audio_ready per line -> show dialogue, play audio, auto-advance
##   4. Press "Hadithi Mpya" (Next) -> next script, or refresh again

@onready var title_label: Label = %TitleLabel
@onready var status_label: Label = %StatusLabel
@onready var live_label: Label = %LiveLabel
@onready var ticker: Label = %TickerLabel
@onready var offline_banner: Label = %OfflineBanner
@onready var headline_label: Label = %HeadlineLabel
@onready var character_label: Label = %CharacterLabel
@onready var dialogue_label: Label = %DialogueLabel
@onready var emotion_label: Label = %EmotionLabel
@onready var start_button: Button = %StartButton
@onready var listen_button: Button = %ListenButton
@onready var next_button: Button = %NextButton
@onready var vote_panel: PanelContainer = %VotePanel
@onready var vote_row: HBoxContainer = %VoteRow
@onready var msisimko_button: Button = %MsisimkoButton
@onready var furaha_button: Button = %FurahaButton
@onready var wasiwasi_button: Button = %WasiwasiButton
@onready var utulivu_button: Button = %UtulivuButton
@onready var vote_result_label: Label = %VoteResultLabel
@onready var drama: OverlapSpeechPlayer = %DramaPlayer
@onready var operator_button: Button = %OperatorButton
@onready var settings_button: Button = %SettingsButton
@onready var weather_label: Label = %WeatherLabel
@onready var cast_panel: VBoxContainer = %CastPanel

const OPERATOR_SCENE := preload("res://scenes/operator.tscn")
const SETTINGS_SCENE := preload("res://scenes/settings.tscn")
const ToastManagerScene := preload("res://ui/ToastManager.gd")
const LoadingScreenScene := preload("res://ui/LoadingScreen.gd")
const OfflineDetectorScene := preload("res://ui/OfflineDetector.gd")
const SpatialScene := preload("res://audio/SpatialAudioManager.gd")
const OcclusionScene := preload("res://audio/AcousticOcclusion.gd")
const CacheScene := preload("res://storage/OfflineCache.gd")
const BeatTrackerScene := preload("res://camera/BeatTracker.gd")
const ShotComposerScene := preload("res://camera/ShotComposer.gd")
const ProceduralCameraScene := preload("res://camera/ProceduralCamera.gd")
const LightBakerScene := preload("res://environment/LightBaker.gd")
const WeatherShaderScene := preload("res://environment/WeatherShader.gd")
const CrowdGeneratorScene := preload("res://environment/CrowdGenerator.gd")
const CharacterControllerScene := preload("res://characters/CharacterController.gd")

var _scripts: Array = []
var _current_script: Dictionary = {}
var _lines: Array = []
var _audio: Dictionary = {}  # line_index -> AudioStream
var _line_index := 0
var _playing := false
var _voted := false
var _listen_mode := false
var _busy := false
var _queue: Array = []
var _operator_open := false
var _loading: Control
var _toasts: VBoxContainer
var _offline: Node
var _spatial: Node
var _occlusion: Node
var _cache: Node
var _settings: AppSettings
var _settings_open := false
var _weather_mood := 0.0
# Camera systems (Features #12, #13)
var _beat_tracker: Node
var _shot_composer: Node
var _procedural_camera: Node
# Environment systems (Features #29, #30, #31)
var _light_baker: Node
var _weather_shader: Node
var _crowd_generator: Node
# Active character controllers per character_id
var _characters: Dictionary = {}  # character_id -> CharacterController


func _ready() -> void:
	next_button.hide()
	vote_panel.hide()
	_connect_signals()
	_build_feedback_layers()
	status_label.text = "Anza ili usikie habari za leo"
	Network.connect_ws()


func _build_feedback_layers() -> void:
	_loading = LoadingScreenScene.new()
	_loading.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_loading)

	_toasts = ToastManagerScene.new()
	_toasts.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_toasts.offset_top = -120
	_toasts.offset_bottom = -16
	add_child(_toasts)

	_offline = OfflineDetectorScene.new()
	_offline.base_url = Network.base_url
	_offline.api_key = Network.api_key
	add_child(_offline)
	_offline.status_changed.connect(_on_offline_changed)
	_offline.start()

	_spatial = SpatialScene.new()
	add_child(_spatial)
	_occlusion = OcclusionScene.new()
	add_child(_occlusion)

	_cache = CacheScene.new()
	Network.cache = _cache
	add_child(_cache)

	# Camera systems (Features #12, #13)
	_beat_tracker = BeatTrackerScene.new()
	_beat_tracker.name = "BeatTracker"
	add_child(_beat_tracker)
	_shot_composer = ShotComposerScene.new()
	_shot_composer.name = "ShotComposer"
	add_child(_shot_composer)
	_shot_composer.setup(_beat_tracker)
	_procedural_camera = ProceduralCameraScene.new()
	_procedural_camera.name = "ProceduralCamera"
	add_child(_procedural_camera)

	# Environment systems (Features #29, #30, #31)
	_light_baker = LightBakerScene.new()
	_light_baker.name = "LightBaker"
	add_child(_light_baker)
	_weather_shader = WeatherShaderScene.new()
	_weather_shader.name = "WeatherShader"
	add_child(_weather_shader)
	_crowd_generator = CrowdGeneratorScene.new()
	_crowd_generator.name = "CrowdGenerator"
	add_child(_crowd_generator)

	_settings = AppSettings.new()
	_settings.load_settings()
	_settings.changed.connect(_on_settings_changed)
	_apply_settings()

	_fetch_weather()


func _fetch_weather() -> void:
	weather_label.show_unknown()
	Network.fetch_weather()


func _notify(message: String, is_error := false, duration := 3.0) -> void:
	if _settings != null and not _settings.notifications_enabled():
		return
	_toasts.show_message(message, is_error, duration)


func _on_offline_changed(is_offline: bool) -> void:
	Network.set_offline(is_offline)
	offline_banner.visible = is_offline
	if is_offline:
		_notify("Nje ya mtandao — hadithi zilizohifadhiwa zinapatikana", true, 3.0)


func _connect_signals() -> void:
	Network.script_failed.connect(_on_script_failed)
	Network.api_error.connect(_on_api_error)
	Network.script_loaded.connect(_on_script_loaded)
	Network.news_loaded.connect(_on_news_loaded)
	Network.audio_ready.connect(_on_audio_ready)
	Network.ws_connected.connect(_on_ws_connected)
	Network.ws_disconnected.connect(_on_ws_disconnected)
	Network.ws_state_snapshot.connect(_on_ws_state_snapshot)
	Network.ws_script_delta.connect(_on_ws_script_delta)
	Network.vote_result.connect(_on_vote_result)
	Network.influence_loaded.connect(_on_influence_loaded)
	Network.vote_stats_loaded.connect(_on_vote_stats_loaded)
	Network.weather_loaded.connect(_on_weather_loaded)
	drama.line_started.connect(_on_line_started)
	drama.sequence_finished.connect(_on_audio_finished)
	start_button.pressed.connect(_on_start_pressed)
	listen_button.pressed.connect(_on_listen_pressed)
	next_button.pressed.connect(_on_next_pressed)
	operator_button.pressed.connect(_on_operator_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	msisimko_button.pressed.connect(func() -> void: _cast_vote("msisimko"))
	furaha_button.pressed.connect(func() -> void: _cast_vote("furaha"))
	wasiwasi_button.pressed.connect(func() -> void: _cast_vote("wasiwasi"))
	utulivu_button.pressed.connect(func() -> void: _cast_vote("utulivu"))


func _on_listen_pressed() -> void:
	_listen_mode = not _listen_mode
	listen_button.text = "Sikiliza: WASH" if _listen_mode else "Sikiliza"
	if _listen_mode:
		status_label.text = "Sikiliza wash — hadithi mpya zitacheza kiotomatiki"


func _on_operator_pressed() -> void:
	if _operator_open:
		return
	_operator_open = true
	var panel := OPERATOR_SCENE.instantiate()
	add_child(panel)
	panel.tree_exited.connect(func() -> void: _operator_open = false)


func _on_settings_pressed() -> void:
	if _settings_open:
		return
	_settings_open = true
	var panel := SETTINGS_SCENE.instantiate()
	panel.settings = _settings
	add_child(panel)
	panel.tree_exited.connect(func() -> void: _settings_open = false)


func _on_settings_changed() -> void:
	_apply_settings()


func _apply_settings() -> void:
	# Data saving forces low quality; otherwise honour the explicit choice.
	var effective := AppSettings.AudioQuality.LOW if _settings.data_saving_enabled() else _settings.get_quality()
	Network.audio_quality = "low" if effective == AppSettings.AudioQuality.LOW else "high"


func _on_ws_connected() -> void:
	live_label.text = "Moja kwa moja: imeunganishwa"


func _on_ws_disconnected() -> void:
	live_label.text = "Moja kwa moja: imekatika"


func _on_ws_state_snapshot(characters: Dictionary) -> void:
	live_label.text = "Wahusika wapo: %d" % characters.size()
	cast_panel.set_snapshot(characters)


func _on_ws_script_delta(delta: Dictionary) -> void:
	var headline: String = delta.get("headline", "")
	if headline != "":
		live_label.text = "HABARI MPYA: " + headline
		ticker.push(headline)
	cast_panel.apply_deltas(delta.get("characters_delta", []))
	if _listen_mode:
		var script_id: String = delta.get("script_id", "")
		if script_id != "":
			Network.fetch_script(script_id)


func _on_script_loaded(script: Dictionary) -> void:
	# A fetched live script (or regenerated one) arrived. Queue if busy,
	# otherwise play it straight away.
	if script.get("script_id", "") != "":
		_cache.cache_script(script)
		cast_panel.register_script(script)
		_register_characters(script)
		var news_ref: Dictionary = script.get("news_ref", {})
		if news_ref.get("headline", "") != "":
			ticker.push(news_ref["headline"])
	if _busy:
		_queue.append(script)
	else:
		_start_script(script)


func _cast_vote(direction: String) -> void:
	var script_id: String = _current_script.get("script_id", "")
	if script_id == "":
		return
	for button in [msisimko_button, furaha_button, wasiwasi_button, utulivu_button]:
		button.disabled = true
	vote_result_label.text = "Kupiga kura..."
	Network.cast_vote(script_id, direction)


func _on_vote_result(payload: Dictionary) -> void:
	_voted = true
	var winner: String = payload.get("winner", "")
	var total: int = payload.get("total", 0)
	vote_result_label.text = "Ulipiga kura: %s | Ushindi: %s | Jumla: %d" % [
		payload.get("direction", ""),
		winner,
		total,
	]
	Network.fetch_influence()


func _on_influence_loaded(payload: Dictionary) -> void:
	var influenced: int = payload.get("scripts_influenced", 0)
	var client: String = payload.get("client_id", "")
	if vote_result_label.text != "":
		vote_result_label.text += " | Ushawishi: %d" % influenced
	else:
		vote_result_label.text = "Ushawishi wako: %d hadithi" % influenced
	# A client_id back from the server confirms our identity reached it.
	if client != "":
		vote_result_label.text += " (%s)" % client


func _on_weather_loaded(payload: Dictionary) -> void:
	weather_label.show_weather(payload)
	_weather_mood = float(payload.get("mood_offset", 0.0))
	_occlusion.set_weather_bias(_weather_mood)
	# Feed weather to environment systems (Features #29, #30).
	var condition: String = payload.get("condition", "angavu")
	_light_baker.set_weather(condition)
	_light_baker.set_mood_offset(_weather_mood)
	_weather_shader.set_weather(condition)


func _on_start_pressed() -> void:
	start_button.disabled = true
	status_label.text = "Inatafuta habari mpya..."
	Network.refresh_news()


func _on_news_loaded(scripts: Array) -> void:
	_scripts = scripts
	for script in scripts:
		if script.get("script_id", "") != "":
			_cache.cache_script(script)
			cast_panel.register_script(script)
			_register_characters(script)
		var news_ref: Dictionary = script.get("news_ref", {})
		if news_ref.get("headline", "") != "":
			ticker.push(news_ref["headline"])
	if _scripts.is_empty():
		status_label.text = "Hakuna habari mpya sasa. Jaribu tena."
		start_button.disabled = false
		next_button.hide()
		return
	_start_script(_scripts[0])


func _start_script(script: Dictionary) -> void:
	_busy = true
	_current_script = script
	_lines = script.get("lines", [])
	_audio.clear()
	_line_index = 0
	_voted = false
	vote_panel.hide()
	vote_result_label.text = ""
	status_label.text = "Inaandaa sauti..."
	headline_label.text = script.get("news_ref", {}).get("headline", "")
	next_button.hide()
	_loading.set_progress(0, _lines.size())
	_loading.show_screen()
	# Load beat tracker for dramatic pacing.
	_beat_tracker.load_script(script)
	# Set up environment from script metadata.
	var metadata: Dictionary = script.get("metadata", {})
	var tod: String = metadata.get("time_of_day", "mchana")
	_light_baker.set_time_of_day(tod)
	var weather_data: Dictionary = metadata.get("weather", {})
	if not weather_data.is_empty():
		var condition: String = weather_data.get("condition", "angavu")
		_light_baker.set_weather(condition)
		_weather_shader.set_weather(condition)
	# Show how the community is already leaning on this story (if any votes).
	var script_id: String = script.get("script_id", "")
	if Network.is_offline:
		if _has_cached_audio(script_id, _lines.size()):
			_load_cached_audio(script_id)
		else:
			status_label.text = "Hakuna sauti zilizohifadhiwa kwa hadithi hii nje ya mtandao"
			_loading.finish()
			start_button.disabled = false
		return

	Network.fetch_vote_stats(script_id)
	Network.generate_audio(script)


func _has_cached_audio(script_id: String, count: int) -> bool:
	if _cache == null or script_id == "" or count == 0:
		return false
	for i in range(count):
		if _cache.load_audio(script_id, i).is_empty():
			return false
	return true


func _load_cached_audio(script_id: String) -> void:
	for i in range(_lines.size()):
		var bytes: PackedByteArray = _cache.load_audio(script_id, i)
		var stream := AudioStreamWAV.new()
		var loaded: AudioStreamWAV = stream.load_from_buffer(bytes)
		if loaded != null and not bytes.is_empty():
			_on_audio_ready(i, loaded)
		else:
			status_label.text = "Hitilafu ya sauti iliyohifadhiwa"


func _on_vote_stats_loaded(payload: Dictionary) -> void:
	if _current_script.get("script_id", "") != payload.get("script_id", ""):
		return  # Stale response for a story we've moved past.
	var total: int = payload.get("total", 0)
	var winner: String = payload.get("winner", "")
	if total == 0:
		vote_result_label.text = "Hakuna kura bado — kuwa wa kwanza!"
	else:
		vote_result_label.text = "Jumuiya: %d kura | Kiongozi: %s" % [total, winner]


func _on_audio_ready(line_index: int, audio: AudioStream) -> void:
	_audio[line_index] = audio
	_loading.set_progress(_audio.size(), _lines.size())
	if _audio.size() == _lines.size():
		status_label.text = ""
		next_button.show()
		_loading.finish()
		_playing = true
		drama.play(_lines, _audio)


func _on_line_started(index: int) -> void:
	if index >= _lines.size():
		return
	_line_index = index
	var line: Dictionary = _lines[index]
	var char_name := _character_name(line.get("character_id", ""))
	character_label.text = char_name
	dialogue_label.text = line.get("text", "")
	emotion_label.text = "[" + line.get("emotion", "") + "]"
	if line.get("overlap", false):
		status_label.text = "Wanakata mazungumzo..."

	# Spatial + acoustic treatment for this line's voice.
	var voice := drama.get_active_player()
	var char_id: String = line.get("character_id", "")
	var emotion: String = line.get("emotion", "")
	_spatial.apply_to(voice, char_id)
	_occlusion.apply_to(voice, char_id, emotion)

	# Beat tracking — advance the dramatic beat for camera cuts.
	_beat_tracker.advance_line(index)
	_shot_composer.set_active_characters(_count_active_characters())

	# Character controller — notify the speaking character.
	if _characters.has(char_id):
		var ctrl: Node = _characters[char_id]
		if ctrl.has_method("on_line_started"):
			ctrl.on_line_started(emotion)


func _on_audio_finished() -> void:
	_playing = false
	_busy = false
	status_label.text = ""
	# Notify all characters the line ended.
	for char_id in _characters:
		var ctrl: Node = _characters[char_id]
		if ctrl.has_method("on_line_finished"):
			ctrl.on_line_finished()
	if _listen_mode and not _queue.is_empty():
		# Live radio: roll straight into the next queued story.
		_start_script(_queue.pop_front())
	elif not _voted:
		# A story just finished: let the listener steer the community pulse.
		vote_panel.show()
		for button in [msisimko_button, furaha_button, wasiwasi_button, utulivu_button]:
			button.disabled = false


func _on_next_pressed() -> void:
	var idx := _scripts.find(_current_script)
	var next_idx := idx + 1 if idx != -1 else 1
	if next_idx >= _scripts.size():
		status_label.text = "Inatafuta habari mpya..."
		Network.refresh_news()
		return
	_start_script(_scripts[next_idx])


func _character_name(character_id: String) -> String:
	for character in _current_script.get("characters", []):
		if character.get("id", "") == character_id:
			return character.get("name", character_id)
	return character_id


func _on_script_failed(message: String) -> void:
	# Transport-level failures carry no error code.
	_handle_failure(message)


func _on_api_error(error_code: String, _raw_message: String) -> void:
	# Envelope failures carry a machine-readable code; show friendly Swahili text.
	_handle_failure(ErrorCatalog.describe(error_code))


func _handle_failure(message: String) -> void:
	status_label.text = "Hitilafu: " + message
	_notify(message, true)
	_loading.finish()
	start_button.disabled = false
	next_button.hide()

	# Offline recovery: replay the most recently cached story.
	if Network.is_offline:
		var cached: Array = _cache.list_scripts()
		if not cached.is_empty():
			var replay: Dictionary = _cache.load_script(cached[0])
			if not replay.is_empty():
				status_label.text = "Ukirejesha hadithi iliyohifadhiwa..."
				_notify("Hadithi iliyohifadhiwa — inacheza bila mtandao", true, 3.0)
				_start_script(replay)


func _input(event: InputEvent) -> void:
	# Space advances to the next line while playing.
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE and _playing:
			drama.skip()
		elif event.keycode == KEY_N:
			_on_next_pressed()


func _count_active_characters() -> int:
	var seen: Dictionary = {}
	for line in _lines:
		var cid: String = line.get("character_id", "")
		if cid != "":
			seen[cid] = true
	return seen.size()


func _register_characters(script: Dictionary) -> void:
	for char_data: Dictionary in script.get("characters", []):
		var cid: String = char_data.get("id", "")
		if cid == "" or _characters.has(cid):
			continue
		var ctrl: Node = CharacterControllerScene.new()
		ctrl.character_id = cid
		ctrl.age = char_data.get("age", "mtu mzima")
		add_child(ctrl)
		_characters[cid] = ctrl