class_name EyeGazeSystem
extends Node3D
## Feature #9: Micro-Expressions & Eye Gaze.
##
## Controls eye position (gaze direction) on a character that exposes
## `left_eye_pivot` and `right_eye_pivot` Node3D children. Eyes follow a
## target (another character, an off-screen point) with natural drift and
## micro-expression movements. Saccades are timed to feel organic.

signal gaze_changed(character_id: String, direction: Vector3)

const SACCADE_MIN_INTERVAL := 0.4
const SACCADE_MAX_INTERVAL := 3.0
const MICRO_DRIFT_AMPLITUDE := 0.03
const GAZE_SMOOTHING := 0.12

var _character_id: String
var _left_eye: Node3D
var _right_eye: Node3D
var _target: Node3D
var _free_gaze := Vector3.FORWARD
var _current_gaze := Vector3.FORWARD
var _saccade_timer := 0.0
var _drift_offset := Vector2.ZERO
var _drift_timer := 0.0
var _enabled := true


func setup(character_id: String, left_eye: Node3D, right_eye: Node3D) -> void:
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

	var desired := _target.global_position if _target else _free_gaze
	_current_gaze = _current_gaze.lerp(desired, GAZE_SMOOTHING)
	_apply_gaze(_current_gaze)


func set_target(node: Node3D) -> void:
	_target = node


func set_free_gaze(direction: Vector3) -> void:
	_free_gaze = direction.normalized()
	_target = null


func set_enabled(enabled: bool) -> void:
	_enabled = enabled


func _do_saccade() -> void:
	# Quick eye jump — saccade — towards the target with some randomness.
	if _target != null:
		var to_target := _target.global_position - _current_gaze
		_current_gaze += to_target.normalized() * randf_range(0.05, 0.15)
	else:
		_current_gaze += Vector3(randf_range(-0.1, 0.1), randf_range(-0.05, 0.05), 0)
	gaze_changed.emit(_character_id, _current_gaze)


func _micro_drift() -> void:
	_drift_offset = Vector2(randf_range(-MICRO_DRIFT_AMPLITUDE, MICRO_DRIFT_AMPLITUDE),
		randf_range(-MICRO_DRIFT_AMPLITUDE, MICRO_DRIFT_AMPLITUDE))


func _apply_gaze(direction: Vector3) -> void:
	var look := direction.normalized()
	if _left_eye != null:
		_left_eye.rotation.y = lerpf(_left_eye.rotation.y, look.x, 0.15)
		_left_eye.rotation.x = lerpf(_left_eye.rotation.x, -look.y, 0.15)
	if _right_eye != null:
		_right_eye.rotation.y = lerpf(_right_eye.rotation.y, look.x, 0.15)
		_right_eye.rotation.x = lerpf(_right_eye.rotation.x, -look.y, 0.15)


func _reset_saccade() -> void:
	_saccade_timer = randf_range(SACCADE_MIN_INTERVAL, SACCADE_MAX_INTERVAL)
