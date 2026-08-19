class_name IdleGenerator
extends Node
## Feature #18: Procedural Idle.
##
## Adds subtle, natural idle movement to characters when they are not
## speaking or walking. Sways the body slightly, shifts weight, and
## adjusts head rotation to simulate breathing and attention shifts.
## Elimicates the "frozen statue" look of characters between dialogue.

const SWAY_AMPLITUDE := 0.02
const SWAY_SPEED := 0.8
const BREATH_AMPLITUDE := 0.01
const BREATH_SPEED := 1.5
const HEAD_DRIFT_AMPLITUDE := 0.03
const HEAD_DRIFT_SPEED := 0.4

var _character_id: String
var _body: Node3D
var _head: Node3D
var _time := 0.0
var _active := true
var _sway_offset := Vector2.ZERO
var _breath_offset := 0.0


func setup(character_id: String, body: Node3D, head: Node3D = null) -> void:
	_character_id = character_id
	_body = body
	_head = head


func set_active(active: bool) -> void:
	_active = active
	if not active and _body != null:
		_body.rotation = Vector3.ZERO


func _process(delta: float) -> void:
	if not _active or _body == null:
		return
	_time += delta
	var sway_x := sin(_time * SWAY_SPEED) * SWAY_AMPLITUDE
	var sway_z := cos(_time * SWAY_SPEED * 0.7) * SWAY_AMPLITUDE * 0.5
	_body.rotation.x += sway_x * delta
	_body.rotation.z += sway_z * delta
	_breath_offset = sin(_time * BREATH_SPEED) * BREATH_AMPLITUDE
	_body.position.y += _breath_offset * delta
	if _head != null:
		var head_x := sin(_time * HEAD_DRIFT_SPEED * 1.3) * HEAD_DRIFT_AMPLITUDE
		var head_y := cos(_time * HEAD_DRIFT_SPEED) * HEAD_DRIFT_AMPLITUDE * 0.5
		_head.rotation.x += head_x * delta
		_head.rotation.y += head_y * delta
