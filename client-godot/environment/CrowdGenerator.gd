class_name CrowdGenerator
extends Node
## Feature #31: Autonomous Crowd (2D).

signal crowd_spawned(count: int)

const MAX_CROWD := 30
const WANDER_RADIUS := 120.0
const WANDER_SPEED := 20.0
const WANDER_INTERVAL_MIN := 3.0
const WANDER_INTERVAL_MAX := 8.0

var _crowd_root: Node2D
var _crowd_scene: PackedScene
var _members: Array[Node2D] = []
var _targets: Array[Vector2] = []
var _timers: Array[float] = []
var _density: int = 10
var _enabled := true

var is_configured := false


func setup(crowd_root: Node2D, crowd_scene: PackedScene) -> void:
	_crowd_root = crowd_root
	_crowd_scene = crowd_scene
	is_configured = true
	_rebuild()


func set_density(count: int) -> void:
	_density = clampi(count, 0, MAX_CROWD)
	_rebuild()


func set_enabled(enabled: bool) -> void:
	_enabled = enabled
	for member in _members:
		member.visible = enabled


func get_density() -> int:
	return _density


func get_member_count() -> int:
	return _members.size()


func _ready() -> void:
	_rebuild()


func _process(delta: float) -> void:
	if not _enabled:
		return
	for i in range(_members.size()):
		_timers[i] -= delta
		if _timers[i] <= 0.0:
			_new_target(i)
			_timers[i] = randf_range(WANDER_INTERVAL_MIN, WANDER_INTERVAL_MAX)
		_move_towards(i, delta)


func _rebuild() -> void:
	for member in _members:
		if member != null and is_instance_valid(member):
			member.queue_free()
	_members.clear()
	_targets.clear()
	_timers.clear()

	if _crowd_scene == null or _crowd_root == null:
		return

	for i in range(_density):
		var member: Node2D = _crowd_scene.instantiate() as Node2D
		if member == null:
			continue
		var angle := randf() * TAU
		var radius := randf_range(20.0, WANDER_RADIUS)
		var pos := Vector2(cos(angle) * radius, sin(angle) * radius)
		member.position = pos
		member.rotation = randf() * TAU
		_crowd_root.add_child(member)
		_members.append(member)
		_targets.append(pos)
		_timers.append(randf_range(WANDER_INTERVAL_MIN, WANDER_INTERVAL_MAX))
	crowd_spawned.emit(_members.size())


func _new_target(index: int) -> void:
	var angle := randf() * TAU
	var radius := randf_range(20.0, WANDER_RADIUS)
	_targets[index] = Vector2(cos(angle) * radius, sin(angle) * radius)


func _move_towards(index: int, delta: float) -> void:
	if index >= _members.size():
		return
	var member := _members[index]
	if member == null or not is_instance_valid(member):
		return
	var to_target := _targets[index] - member.position
	if to_target.length() < 3.0:
		return
	var direction := to_target.normalized()
	member.position += direction * WANDER_SPEED * delta
	member.rotation = lerp_angle(member.rotation, direction.angle(), 0.1)
