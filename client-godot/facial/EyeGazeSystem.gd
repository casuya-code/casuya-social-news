class_name EyeGazeSystem
extends Node2D
## Feature #9: Micro-Expressions & Eye Gaze (2D).
##
## Controls eye position (gaze direction) on a 2D character. Eyes follow a
## target with natural drift and micro-expression movements.

signal gaze_changed(character_id: String, direction: Vector2)

const SACCADE_MIN_INTERVAL := 0.4
const SACCADE_MAX_INTERVAL := 3.0
const MICRO_DRIFT_AMPLITUDE := 0.03
const GAZE_SMOOTHING := 0.12

var _character_id: String
var _left_eye: Node2D
var _right_eye: Node2D
var _target: Node2D
var _free_gaze := Vector2.RIGHT
var _current_gaze := Vector2.RIGHT
var _saccade_timer := 0.0
var _drift_offset := Vector2.ZERO
var _drift_timer := 0.0
var _enabled := true


func setup(character_id: String, left_eye: Node2D, right_eye: Node2D) -> void:
	_character_id = character_id
	_left_eye = left_eye
	_right_eye = right_eye
	_reset_saccade()


func _ready() -> void:
	_reset_saccade()


func _process(delta: float) -> void:
	if not _enabled:
		return
	_saccade_timer -= delta
	_drift_timer -= delta
	if _saccade_timer <= 0.0:
		_do_saccade()
		_reset_saccade()
	if _drift_timer <= 0.0:
		_micro_drift()
		_drift_timer = randf_range(0.3, 1.0)

	var desired := _target.global_position if _target != null else _free_gaze
	_current_gaze = _current_gaze.lerp(desired, GAZE_SMOOTHING)
	_apply_gaze(_current_gaze)


func set_target(node: Node2D) -> void:
	_target = node


func set_free_gaze(direction: Vector2) -> void:
	_free_gaze = direction.normalized() if direction != Vector2.ZERO else Vector2.RIGHT
	_target = null


func set_enabled(enabled: bool) -> void:
	_enabled = enabled


func _do_saccade() -> void:
	if _target != null:
		var to_target := _target.global_position - _current_gaze
		if to_target.length() > 0.001:
			_current_gaze += to_target.normalized() * randf_range(0.05, 0.15)
	else:
		_current_gaze += Vector2(randf_range(-0.1, 0.1), randf_range(-0.05, 0.05))
	gaze_changed.emit(_character_id, _current_gaze)


func _micro_drift() -> void:
	_drift_offset = Vector2(
		randf_range(-MICRO_DRIFT_AMPLITUDE, MICRO_DRIFT_AMPLITUDE),
		randf_range(-MICRO_DRIFT_AMPLITUDE, MICRO_DRIFT_AMPLITUDE)
	)


func _apply_gaze(direction: Vector2) -> void:
	var look := direction.normalized() if direction != Vector2.ZERO else Vector2.RIGHT
	if _left_eye != null:
		_left_eye.rotation = lerpf(_left_eye.rotation, look.x * 0.2, 0.15)
	if _right_eye != null:
		_right_eye.rotation = lerpf(_right_eye.rotation, look.x * 0.2, 0.15)


func _reset_saccade() -> void:
	_saccade_timer = randf_range(SACCADE_MIN_INTERVAL, SACCADE_MAX_INTERVAL)
