class_name IdleGenerator
extends Node
## Feature #18: Procedural Idle (2D).
##
## Adds subtle, natural idle movement to characters when they are not
## speaking or walking.

const SWAY_AMPLITUDE := 0.02
const SWAY_SPEED := 0.8
const BREATH_AMPLITUDE := 1.0
const BREATH_SPEED := 1.5
const HEAD_DRIFT_AMPLITUDE := 0.03
const HEAD_DRIFT_SPEED := 0.4

var _character_id: String
var _body: Node2D
var _head: Node2D
var _time := 0.0
var _active := true
var _breath_offset := 0.0


func setup(character_id: String, body: Node2D, head: Node2D = null) -> void:
	_character_id = character_id
	_body = body
	_head = head


func set_active(active: bool) -> void:
	_active = active
	if not active and _body != null:
		_body.rotation = 0.0


func _process(delta: float) -> void:
	if not _active or _body == null:
		return
	_time += delta
	var sway := sin(_time * SWAY_SPEED) * SWAY_AMPLITUDE
	_body.rotation += sway * delta
	_breath_offset = sin(_time * BREATH_SPEED) * BREATH_AMPLITUDE
	_body.position.y += _breath_offset * delta
	if _head != null:
		var head_rot := sin(_time * HEAD_DRIFT_SPEED * 1.3) * HEAD_DRIFT_AMPLITUDE
		_head.rotation += head_rot * delta
