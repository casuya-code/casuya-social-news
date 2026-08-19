class_name ShotComposer
extends Node
## Shot composition logic — determines which camera shot to use based on
## the current dramatic beat and the number of active speakers. Works
## alongside ProceduralCamera and BeatTracker.
##
## Single responsibility: scene context -> camera composition choice.

enum ShotType { WIDE, MEDIUM, CLOSE_UP, OVER_SHOULDER, CUT_AWAY }

const TWO_SPEAKER_SHOTS := [ShotType.OVER_SHOULDER, ShotType.CLOSE_UP]
const SOLO_SHOTS := [ShotType.CLOSE_UP, ShotType.MEDIUM]

var _beat_tracker: Node
var _active_characters: int = 1
var _current_shot: int = ShotType.WIDE
var _shot_duration := 4.0
var _shot_timer := 0.0


func setup(beat_tracker: Node) -> void:
	_beat_tracker = beat_tracker
	if beat_tracker != null:
		_beat_tracker.beat_changed.connect(_on_beat_changed)


func _process(delta: float) -> void:
	_shot_timer -= delta
	if _shot_timer <= 0.0:
		_recompose()


func set_active_characters(count: int) -> void:
	_active_characters = maxi(count, 1)


func get_current_shot() -> int:
	return _current_shot


func get_shot_name(shot: int) -> String:
	match shot:
		ShotType.WIDE:
			return "Pana"
		ShotType.MEDIUM:
			return "Wastani"
		ShotType.CLOSE_UP:
			return "Karibu"
		ShotType.OVER_SHOULDER:
			return "Mkia"
		ShotType.CUT_AWAY:
			return "Kata"
		_:
			return "Pana"


func _on_beat_changed(_beat_index: int, beat_type: String, intensity: float) -> void:
	_recompose_for_beat(beat_type, intensity)


func _recompose() -> void:
	var intensity := 0.3
	if _beat_tracker != null:
		intensity = _beat_tracker.get_intensity()
	_recompose_for_beat(_beat_tracker.get_beat_type() if _beat_tracker else "CALM", intensity)


func _recompose_for_beat(beat_type: String, intensity: float) -> void:
	var previous := _current_shot
	match beat_type:
		"CALM":
			_current_shot = ShotType.WIDE if _active_characters > 1 else ShotType.MEDIUM
			_shot_duration = 5.0
		"TENSION":
			_current_shot = ShotType.MEDIUM
			_shot_duration = 3.5
		"CLIMAX":
			_current_shot = ShotType.CLOSE_UP if _active_characters == 1 else ShotType.OVER_SHOULDER
			_shot_duration = 2.0
		"RESOLUTION":
			_current_shot = ShotType.WIDE
			_shot_duration = 6.0
		"SILENCE":
			_current_shot = ShotType.CUT_AWAY
			_shot_duration = 4.0
	if _current_shot != previous:
		_shot_timer = _shot_duration
