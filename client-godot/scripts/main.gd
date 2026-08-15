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
@onready var offline_banner: Label = %OfflineBanner
@onready var headline_label: Label = %HeadlineLabel
@onready var character_label: Label = %CharacterLabel
@onready var dialogue_label: Label = %DialogueLabel
@onready var emotion_label: Label = %EmotionLabel
@onready var start_button: Button = %StartButton
@onready var listen_button: Button = %ListenButton
@onready var next_button: Button = %NextButton
@onready var vote_row: HBoxContainer = %VoteRow
@onready var msisimko_button: Button = %MsisimkoButton
@onready var furaha_button: Button = %FurahaButton
@onready var wasiwasi_button: Button = %WasiwasiButton
@onready var utulivu_button: Button = %UtulivuButton
@onready var vote_result_label: Label = %VoteResultLabel
@onready var drama: OverlapSpeechPlayer = %DramaPlayer
@onready var operator_button: Button = %OperatorButton
@onready var settings_button: Button = %SettingsButton

const OPERATOR_SCENE := preload("res://scenes/operator.tscn")
const SETTINGS_SCENE := preload("res://scenes/settings.tscn")
const ToastManagerScene := preload("res://ui/ToastManager.gd")
const LoadingScreenScene := preload("res://ui/LoadingScreen.gd")
const OfflineDetectorScene := preload("res://ui/OfflineDetector.gd")
const SpatialScene := preload("res://audio/SpatialAudioManager.gd")
const OcclusionScene := preload("res://audio/AcousticOcclusion.gd")
const CacheScene := preload("res://storage/OfflineCache.gd")

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


func _ready() -> void:
	next_button.hide()
	vote_row.hide()
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

	_settings = AppSettings.new()
	_settings.load_settings()
	_settings.changed.connect(_on_settings_changed)
	_apply_settings()


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
	Network.script_loaded.connect(_on_script_loaded)
	Network.news_loaded.connect(_on_news_loaded)
	Network.audio_ready.connect(_on_audio_ready)
	Network.ws_connected.connect(_on_ws_connected)
	Network.ws_disconnected.connect(_on_ws_disconnected)
	Network.ws_state_snapshot.connect(_on_ws_state_snapshot)
	Network.ws_script_delta.connect(_on_ws_script_delta)
	Network.vote_result.connect(_on_vote_result)
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


func _on_ws_script_delta(delta: Dictionary) -> void:
	var headline: String = delta.get("headline", "")
	if headline != "":
		live_label.text = "HABARI MPYA: " + headline
	if _listen_mode:
		var script_id: String = delta.get("script_id", "")
		if script_id != "":
			Network.fetch_script(script_id)


func _on_script_loaded(script: Dictionary) -> void:
	# A fetched live script (or regenerated one) arrived. Queue if busy,
	# otherwise play it straight away.
	if script.get("script_id", "") != "":
		_cache.cache_script(script)
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


func _on_start_pressed() -> void:
	start_button.disabled = true
	status_label.text = "Inatafuta habari mpya..."
	Network.refresh_news()


func _on_news_loaded(scripts: Array) -> void:
	_scripts = scripts
	for script in scripts:
		if script.get("script_id", "") != "":
			_cache.cache_script(script)
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
	vote_row.hide()
	vote_result_label.text = ""
	status_label.text = "Inaandaa sauti..."
	headline_label.text = script.get("news_ref", {}).get("headline", "")
	next_button.hide()
	_loading.set_progress(0, _lines.size())
	_loading.show_screen()
	Network.generate_audio(script)


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


func _on_audio_finished() -> void:
	_playing = false
	_busy = false
	status_label.text = ""
	if _listen_mode and not _queue.is_empty():
		# Live radio: roll straight into the next queued story.
		_start_script(_queue.pop_front())
	elif not _voted:
		# A story just finished: let the listener steer the community pulse.
		vote_row.show()
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