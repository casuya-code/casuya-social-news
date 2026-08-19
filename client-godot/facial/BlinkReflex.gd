class_name BlinkReflex
extends Node
## Feature #11: Sensory Blink Reflex.
##
## Automates eye blinks on a character mesh that exposes `blink_weight`
## (blend shape). Blinks at a natural rhythm with occasional spontaneous
## reflex blinks. Responds to bright flashes (audio peaks) by triggering
## an immediate reflex blink.

signal blink_triggered(character_id: String)

const BASE_BLINK_INTERVAL := 4.0
const BLINK_VARIANCE := 2.5
const BLINK_DURATION := 0.12
const REFLEX_COOLDOWN := 0.8

var _character_id: String
var _eye_node: Node3D
var _blink_timer := 0.0
var _next_blink := 0.0
var _blinking := false
var _blink_elapsed := 0.0
var _reflex_cooldown := 0.0
var _enabled := true


func setup(character_id: String, eye_node: Node3D) -> void:
	_character_id = character_id
	_eye_node = eye_node
	_reset_timer()


func _ready() -> void:
	_reset_timer()


func _process(delta: float) -> void:
	if not _enabled or _eye_node == null:
		return
	_reflex_cooldown = maxf(_reflex_cooldown - delta, 0.0)
	_blink_timer -= delta
	if _blinking:
		_blink_elapsed += delta
		var progress := _blink_elapsed / BLINK_DURATION
		if progress >= 1.0:
			_blinking = false
			_apply_blink(0.0)
		else:
			_apply_blink(sin(progress * PI))
	elif _blink_timer <= 0.0:
		_start_blink()
		_reset_timer()


## Trigger an immediate reflex blink (e.g., from a bright flash or loud sound).
func trigger_reflex() -> void:
	if _reflex_cooldown > 0.0:
		return
	_reflex_cooldown = REFLEX_COOLDOWN
	_start_blink()


func set_enabled(enabled: bool) -> void:
	_enabled = enabled
	if not enabled:
		_apply_blink(0.0)


func _start_blink() -> void:
	_blinking = true
	_blink_elapsed = 0.0
	blink_triggered.emit(_character_id)


func _apply_blink(weight: float) -> void:
	if _eye_node != null and _eye_node.has_method("set_blink_weight"):
		_eye_node.set_blink_weight(weight)


func _reset_timer() -> void:
	_blink_timer = BASE_BLINK_INTERVAL + randf_range(-BLINK_VARIANCE, BLINK_VARIANCE)
