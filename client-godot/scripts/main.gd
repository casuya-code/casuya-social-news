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
@onready var headline_label: Label = %HeadlineLabel
@onready var character_label: Label = %CharacterLabel
@onready var dialogue_label: Label = %DialogueLabel
@onready var emotion_label: Label = %EmotionLabel
@onready var start_button: Button = %StartButton
@onready var next_button: Button = %NextButton
@onready var player: AudioStreamPlayer = %AudioPlayer

var _scripts: Array = []
var _current_script: Dictionary = {}
var _lines: Array = []
var _audio: Dictionary = {}  # line_index -> AudioStream
var _line_index := 0
var _playing := false


func _ready() -> void:
	next_button.hide()
	_connect_signals()
	status_label.text = "Anza ili usikie habari za leo"


func _connect_signals() -> void:
	Network.script_failed.connect(_on_script_failed)
	Network.news_loaded.connect(_on_news_loaded)
	Network.audio_ready.connect(_on_audio_ready)
	player.finished.connect(_on_audio_finished)
	start_button.pressed.connect(_on_start_pressed)
	next_button.pressed.connect(_on_next_pressed)


func _on_start_pressed() -> void:
	start_button.disabled = true
	status_label.text = "Inatafuta habari mpya..."
	Network.refresh_news()


func _on_news_loaded(scripts: Array) -> void:
	_scripts = scripts
	if _scripts.is_empty():
		status_label.text = "Hakuna habari mpya sasa. Jaribu tena."
		start_button.disabled = false
		next_button.hide()
		return
	_start_script(_scripts[0])


func _start_script(script: Dictionary) -> void:
	_current_script = script
	_lines = script.get("lines", [])
	_audio.clear()
	_line_index = 0
	status_label.text = "Inaandaa sauti..."
	headline_label.text = script.get("news_ref", {}).get("headline", "")
	next_button.hide()
	Network.generate_audio(script)


func _on_audio_ready(line_index: int, audio: AudioStream) -> void:
	_audio[line_index] = audio
	if _audio.size() == _lines.size():
		status_label.text = ""
		next_button.show()
		_play_line(0)


func _play_line(index: int) -> void:
	if index >= _lines.size():
		return
	_line_index = index
	var line: Dictionary = _lines[index]
	var char_name := _character_name(line.get("character_id", ""))
	character_label.text = char_name
	dialogue_label.text = line.get("text", "")
	emotion_label.text = "[" + line.get("emotion", "") + "]"
	var stream: AudioStream = _audio.get(index)
	if stream:
		_playing = true
		player.stream = stream
		player.play()


func _on_audio_finished() -> void:
	_playing = false
	var next := _line_index + 1
	if next < _lines.size():
		_play_line(next)


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
	start_button.disabled = false
	next_button.hide()


func _input(event: InputEvent) -> void:
	# Space advances to the next line while playing.
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE and _playing:
			player.stop()
			_on_audio_finished()
		elif event.keycode == KEY_N:
			_on_next_pressed()