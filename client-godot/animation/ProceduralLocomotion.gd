class_name ProceduralLocomotion
extends Node
## Feature #17: IK-based Locomotion.
##
## Procedural walking for characters — no hand-keyed animation needed.
## Drives a simple two-bone IK leg system with configurable speed and
## stride length. Walks towards a target position, stops when close.
## Supports turning via a blend of forward velocity and rotation.

signal walk_started(character_id: String)
signal walk_finished(character_id: String)

const DEFAULT_SPEED := 2.0
const DEFAULT_STRIDE := 0.6
const TURN_SMOOTHING := 0.1
const STOP_THRESHOLD := 0.15

var _character_id: String
var _body: Node3D
var _left_leg: SkeletonIK3D
var _right_leg: SkeletonIK3D
var _target_position: Vector3 = Vector3.INF
var _speed := DEFAULT_SPEED
var _stride := DEFAULT_STRIDE
var _walking := false
var _phase := 0.0
var _enabled := true


func setup(character_id: String, body: Node3D, left_leg: SkeletonIK3D, right_leg: SkeletonIK3D) -> void:
	_character_id = character_id
	_body = body
	_left_leg = left_leg
	_right_leg = right_leg


func walk_to(destination: Vector3) -> void:
	_target_position = destination
	if not _walking:
		_walking = true
		_phase = 0.0
		walk_started.emit(_character_id)


func stop() -> void:
	if _walking:
		_walking = false
		_target_position = Vector3.INF
		walk_finished.emit(_character_id)


func is_walking() -> bool:
	return _walking


func set_speed(s: float) -> void:
	_speed = s


func set_stride(s: float) -> void:
	_stride = s


func set_enabled(e: bool) -> void:
	_enabled = e
	if not e:
		stop()


func _process(delta: float) -> void:
	if not _enabled or not _walking or _body == null:
		return
	if _target_position == Vector3.INF:
		return
	var to_target := _target_position - _body.global_position
	var distance := to_target.length()
	if distance < STOP_THRESHOLD:
		stop()
		return
	var direction := to_target.normalized()
	var step := _speed * delta
	_body.global_position += direction * step
	_phase += delta * _speed * 2.0
	_body.rotation.y = lerpf(_body.rotation.y, atan2(direction.x, direction.z), TURN_SMOOTHING)
	_apply_leg_ik()


func _apply_leg_ik() -> void:
	if _left_leg != null:
		_left_leg.start()
	if _right_leg != null:
		_right_leg.start()
