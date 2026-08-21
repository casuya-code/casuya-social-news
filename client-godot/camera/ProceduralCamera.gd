class_name ProceduralCamera
extends Node3D
## Feature #12: Procedural Camera (Kamera ya Kisanii).
##
## Drives a3D camera based on the ShotComposer's cinematic decisions.
## Reads shot type from the ShotComposer to position the camera
## (wide / medium / close-up / over-shoulder / cutaway) and smoothly
## transitions between positions. Falls back to autonomous wide/close-up
## cycling when no ShotComposer is connected.

signal shot_changed(shot_type: int, shot_name: String)

@export_group("Camera Settings")
@export var target_node: Node3D = null
@export var shot_distance: float = 10.0
@export var close_up_distance: float = 3.0
@export var medium_distance: float = 7.0
@export var wide_distance: float = 15.0
@export var transition_speed: float = 5.0

@export_group("Shot Types")
@export var current_shot: int = 0  # 0=wide, 1=close-up
@export var shot_timer: float = 0.0
@export var shot_duration: float = 5.0

var _shot_composer: Node  # ShotComposer reference
var _target_distance := 10.0
var _target_height := 2.0


func _ready() -> void:
	shot_timer = shot_duration


func setup_composer(shot_composer: Node) -> void:
	"""Connect to a ShotComposer to drive camera positions."""
	_shot_composer = shot_composer
	if _shot_composer != null and _shot_composer.has_signal("shot_changed"):
		_pass  # ShotComposer doesn't emit shot_changed yet; we poll.


func _physics_process(delta: float) -> void:
	# If connected to a ShotComposer, read its current shot instead of
	# independent cycling.
	if _shot_composer != null:
		var composer_shot: int = _shot_composer.get_current_shot()
		_match_composer_shot(composer_shot)
	else:
		# Autonomous fallback: cycle wide ↔ close-up.
		shot_timer -= delta
		if shot_timer <= 0.0:
			current_shot = (current_shot + 1) % 2
			if current_shot == 0:
				_target_distance = wide_distance
				_target_height = 2.0
			else:
				_target_distance = close_up_distance
				_target_height = 1.5
			shot_timer = shot_duration


func _match_composer_shot(composer_shot: int) -> void:
	"""Map a ShotComposer ShotType enum to camera distance + height."""
	var ShotType = preload("res://camera/ShotComposer.gd").ShotType
	var prev := current_shot
	match composer_shot:
		ShotType.WIDE:
			_target_distance = wide_distance
			_target_height = 2.0
			current_shot = 0
		ShotType.MEDIUM:
			_target_distance = medium_distance
			_target_height = 1.8
			current_shot = 0
		ShotType.CLOSE_UP:
			_target_distance = close_up_distance
			_target_height = 1.5
			current_shot = 1
		ShotType.OVER_SHOULDER:
			_target_distance = close_up_distance * 1.2
			_target_height = 1.6
			current_shot = 1
		ShotType.CUT_AWAY:
			_target_distance = wide_distance * 1.3
			_target_height = 3.0
			current_shot = 0
	if current_shot != prev:
		shot_changed.emit(current_shot, get_shot_name(current_shot))


func set_target(node: Node3D) -> void:
	target_node = node


func switch_to_closeup() -> void:
	current_shot = 1
	_target_distance = close_up_distance
	_target_height = 1.5
	shot_timer = 0.0


func switch_to_wide() -> void:
	current_shot = 0
	_target_distance = wide_distance
	_target_height = 2.0
	shot_timer = 0.0


func get_shot_name(shot: int) -> String:
	if shot == 1:
		return "Karibu"
	return "Pana"


func _process(delta: float) -> void:
	# Smoothly interpolate toward the target distance.
	shot_distance = lerpf(shot_distance, _target_distance, delta * transition_speed)

	if target_node != null and target_node.is_inside_tree():
		var cam_pos := target_node.global_position + Vector3(0, _target_height, -shot_distance)
		global_position = global_position.lerp(cam_pos, delta * transition_speed)

		# Look at target.
		var target_pos: Vector3 = target_node.global_position
		if target_node is Camera3D:
			var forward: Vector3 = -target_node.global_transform.basis.z
			look_at(target_pos + forward * 2.0 + Vector3(0, 1, 0))
		else:
			look_at(target_pos + Vector3(0, 1, 0))