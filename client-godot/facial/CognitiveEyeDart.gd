class_name CognitiveEyeDart
extends Node
## Feature #10: Eye-Darting (thinking / cognitive load).
##
## Drives rapid micro-saccades (eye darting) when a character is thinking,
## calculating, or under cognitive load. The darts are horizontal micro-
## movements that convey the internal mental process of the character.
## Activated/deactivated via `set_active()` — typically triggered by the
## `anafikiria` or `anahofia` emotion tags.

signal eye_dart(character_id: String, direction: Vector2)

const DART_SPEED := 0.06
const DART_AMPLITUDE := 0.08
const DART_INTERVAL_MIN := 0.08
const DART_INTERVAL_MAX := 0.22
const DART_DAMPING := 0.85

var _character_id: String
var _eye_node: Node3D
var _active := false
var _dart_timer := 0.0
var _dart_offset := Vector2.ZERO
var _target_offset := Vector2.ZERO


func setup(character_id: String, eye_node: Node3D) -> void:
	_character_id = character_id
	_eye_node = eye_node


func set_active(active: bool) -> void:
	_active = active
	if not active:
		_dart_offset = Vector2.ZERO
		_apply(Vector2.ZERO)


func is_active() -> bool:
	return _active


func _process(delta: float) -> void:
	if not _active or _eye_node == null:
		return
	_dart_timer -= delta
	if _dart_timer <= 0.0:
		_new_dart()
		_dart_timer = randf_range(DART_INTERVAL_MIN, DART_INTERVAL_MAX)
	_dart_offset = _dart_offset.lerp(_target_offset, DART_SPEED / delta)
	_target_offset *= DART_DAMPING
	_apply(_dart_offset)


func _new_dart() -> void:
	_target_offset = Vector2(
		randf_range(-DART_AMPLITUDE, DART_AMPLITUDE),
		randf_range(-DART_AMPLITUDE * 0.3, DART_AMPLITUDE * 0.3)
	)
	eye_dart.emit(_character_id, _target_offset)


func _apply(offset: Vector2) -> void:
	if _eye_node != null and _eye_node.has_method("set_eye_offset"):
		_eye_node.set_eye_offset(offset)
	elif _eye_node != null:
		_eye_node.rotation.y += offset.x * 0.1
		_eye_node.rotation.x += offset.y * 0.1
