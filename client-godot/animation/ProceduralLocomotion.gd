class_name ProceduralLocomotion
extends Node
## Feature #17: Locomotion (2D).
##
## Simple 2D procedural movement towards a target position.

signal walk_started(character_id: String)
signal walk_finished(character_id: String)

const DEFAULT_SPEED := 120.0
const DEFAULT_STRIDE := 20.0
const TURN_SMOOTHING := 0.1
const STOP_THRESHOLD := 4.0

var _character_id: String
var _body: Node2D
var _target_position: Vector2 = Vector2.INF
var _speed := DEFAULT_SPEED
var _stride := DEFAULT_STRIDE
var _walking := false
var _phase := 0.0
var _enabled := true


func setup(character_id: String, body: Node2D, _left_leg: Node = null, _right_leg: Node = null) -> void:
	_character_id = character_id
	_body = body


func walk_to(destination: Vector2) -> void:
	_target_position = destination
	if not _walking:
		_walking = true
		_phase = 0.0
		walk_started.emit(_character_id)


func stop() -> void:
	if _walking:
		_walking = false
		_target_position = Vector2.INF
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
	if _target_position == Vector2.INF:
		return
	var to_target := _target_position - _body.global_position
	var distance := to_target.length()
	if distance < STOP_THRESHOLD:
		stop()
		return
	var direction := to_target.normalized()
	var step: float = _speed * delta
	_body.global_position += direction * step
	_phase += delta * _speed * 0.02
	_body.rotation = lerp_angle(_body.rotation, direction.angle(), TURN_SMOOTHING)
