class_name CrowdGenerator
extends Node
## Feature #31: Autonomous Crowd.
##
## Spawns and manages background crowd characters for scene environments.
## Crowd members are simple low-poly meshes with randomised appearance
## and autonomous idle movement (wandering, turning) to give the scene
## a living, populated feel. Density is adjustable per scene.

signal crowd_spawned(count: int)

const MAX_CROWD := 30
const WANDER_RADIUS := 8.0
const WANDER_SPEED := 0.4
const WANDER_INTERVAL_MIN := 3.0
const WANDER_INTERVAL_MAX := 8.0

var _crowd_root: Node3D
var _crowd_mesh: PackedScene
var _members: Array[Node3D] = []
var _targets: Array[Vector3] = []
var _timers: Array[float] = []
var _density: int = 10
var _enabled := true


## Whether setup() has been called with valid root + mesh.
var is_configured := false


func setup(crowd_root: Node3D, crowd_mesh: PackedScene) -> void:
	_crowd_root = crowd_root
	_crowd_mesh = crowd_mesh
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

	if _crowd_mesh == null or _crowd_root == null:
		return

	for i in range(_density):
		var member: Node3D = _crowd_mesh.instantiate() as Node3D
		if member == null:
			continue
		var angle := randf() * TAU
		var radius := randf_range(1.0, WANDER_RADIUS)
		var pos := Vector3(cos(angle) * radius, 0, sin(angle) * radius)
		member.position = pos
		member.rotation.y = randf() * TAU
		_crowd_root.add_child(member)
		_members.append(member)
		_targets.append(pos)
		_timers.append(randf_range(WANDER_INTERVAL_MIN, WANDER_INTERVAL_MAX))
	crowd_spawned.emit(_members.size())


func _new_target(index: int) -> void:
	var angle := randf() * TAU
	var radius := randf_range(1.0, WANDER_RADIUS)
	_targets[index] = Vector3(cos(angle) * radius, 0, sin(angle) * radius)


func _move_towards(index: int, delta: float) -> void:
	if index >= _members.size():
		return
	var member := _members[index]
	if member == null or not is_instance_valid(member):
		return
	var to_target := _targets[index] - member.position
	if to_target.length() < 0.3:
		return
	var direction := to_target.normalized()
	member.position += direction * WANDER_SPEED * delta
	member.rotation.y = lerpf(member.rotation.y, atan2(direction.x, direction.z), 0.1)
