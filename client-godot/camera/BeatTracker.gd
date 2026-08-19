class_name BeatTracker
extends Node
## Feature #13: Cinematic Beat Tracking.
##
## Tracks the dramatic beat (pacing) of a scene — beat transitions drive
## camera cuts, music cues, and scene transitions. A "beat" is defined by
## dialogue intensity changes: emotion shifts, overlap flags, and silence
## gaps between lines. The tracker emits beat signals that the camera and
## audio systems consume.

signal beat_changed(beat_index: int, beat_type: String, intensity: float)

enum BeatType { CALM, TENSION, CLIMAX, RESOLUTION, SILENCE }

const INTENSITY_SMOOTHING := 0.2

var _lines: Array = []
var _current_beat := 0
var _intensity := 0.0
var _in_silence := false
var _silence_timer := 0.0
var _silence_threshold := 0.5

var _intensity_map := {
	"anaongea_kwa_utulivu": 0.1,
	"anaongea_kwa_huzuni": 0.3,
	"anafikiria": 0.2,
	"anacheka_kwa_dharau": 0.6,
	"anadhihaki": 0.5,
	"anashangaa": 0.8,
	"anakasirika": 0.9,
	"anapiga_kelele": 1.0,
	"anahofia": 0.7,
	"anasikitika": 0.4,
	"anajigamba": 0.6,
	"anaomba_msaada": 0.5,
}


func load_script(script: Dictionary) -> void:
	_lines = script.get("lines", [])
	_current_beat = 0
	_intensity = 0.0
	_in_silence = false
	_emit_beat("CALM", 0.1)


func advance_line(line_index: int) -> void:
	if line_index < 0 or line_index >= _lines.size():
		return
	var line: Dictionary = _lines[line_index]
	var emotion: String = line.get("emotion", "")
	var is_overlap: bool = line.get("overlap", false)
	var target_intensity: float = float(_intensity_map.get(emotion, 0.3))
	if is_overlap:
		target_intensity = minf(target_intensity + 0.2, 1.0)
	_intensity = lerpf(_intensity, target_intensity, INTENSITY_SMOOTHING)
	_in_silence = false

	var beat_type := _classify_beat(_intensity)
	_current_beat = line_index
	_emit_beat(beat_type, _intensity)


func on_silence(duration: float) -> void:
	if duration >= _silence_threshold and not _in_silence:
		_in_silence = true
		_emit_beat("SILENCE", 0.0)


func get_intensity() -> float:
	return _intensity


func get_beat_type() -> String:
	return _classify_beat(_intensity)


func get_beat_index() -> int:
	return _current_beat


func _classify_beat(intensity: float) -> String:
	if intensity < 0.2:
		return "CALM"
	if intensity < 0.5:
		return "TENSION"
	if intensity < 0.8:
		return "CLIMAX"
	return "RESOLUTION" if intensity > 0.9 else "TENSION"


func _emit_beat(beat_type: String, intensity: float) -> void:
	beat_changed.emit(_current_beat, beat_type, intensity)
