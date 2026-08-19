class_name LipsyncController
extends Node
## Feature #7: Adaptive Lipsync.
##
## Drives a simple mouth-shape blend/texture based on audio amplitude and
## phoneme analysis. Works with any 3D character that exposes a
## `mouth_shape_index` property (via ShaderMaterial or blend shapes).
## The controller listens to the active AudioStreamPlayer3D and updates
## the mouth target in real time.

signal mouth_changed(character_id: String, shape: int)

const SHAPES := ["closed", "narrow", "wide", "open", "wide_open"]
const AMPLITUDE_THRESHOLD := 0.08

const PhonemeAnalyzerClass := preload("res://facial/PhonemeAnalyzer.gd")

var _analyzer: RefCounted
var _character_id: String
var _mouth_node: Node3D
var _sample_window: Array = []
var _current_shape := 0
var _smoothed_amplitude := 0.0
var _smoothing := 0.3

var _analyzer_ready := false


func _ready() -> void:
	_analyzer = PhonemeAnalyzerClass.new()
	_analyzer_ready = true


func setup(character_id: String, mouth_node: Node3D) -> void:
	_character_id = character_id
	_mouth_node = mouth_node


## Drive lipsync from the raw amplitude of the playing audio stream. Call
## every frame from the parent character or main scene.
func update_from_amplitude(player: AudioStreamPlayer3D) -> void:
	if player == null or not player.playing:
		_set_shape(0)
		return
	var amp := _player_amplitude(player)
	_smoothed_amplitude = lerpf(_smoothed_amplitude, amp, _smoothing)
	var shape := _amplitude_to_shape(_smoothed_amplitude)
	_set_shape(shape)


## Drive lipsync from a phoneme analysis result (array of {time, phoneme}).
func update_from_phoneme(phoneme: String, _time: float) -> void:
	var shape := _phoneme_to_shape(phoneme)
	_set_shape(shape)


func _set_shape(shape: int) -> void:
	if shape == _current_shape:
		return
	_current_shape = shape
	if _mouth_node != null:
		if _mouth_node.has_method("set_mouth_shape"):
			_mouth_node.set_mouth_shape(shape)
	mouth_changed.emit(_character_id, shape)


func _amplitude_to_shape(amp: float) -> int:
	if amp < AMPLITUDE_THRESHOLD:
		return 0  # closed
	if amp < 0.25:
		return 1  # narrow
	if amp < 0.45:
		return 2  # wide
	if amp < 0.65:
		return 3  # open
	return 4  # wide_open


func _phoneme_to_shape(phoneme: String) -> int:
	match phoneme:
		"X":
			return 0
		"P", "S":
			return 1
		"I":
			return 2
		"E":
			return 3
		"A":
			return 4
		_:
			return 0


func _player_amplitude(player: AudioStreamPlayer3D) -> float:
	if player.stream == null or not player.stream is AudioStreamWAV:
		return 0.0
	# Approximate amplitude from volume_db (linear).
	return clampf(db_to_linear(player.volume_db), 0.0, 1.0)


func get_shape() -> int:
	return _current_shape


func get_amplitude() -> float:
	return _smoothed_amplitude
