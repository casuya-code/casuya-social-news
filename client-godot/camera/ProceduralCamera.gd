class_name ProceduralCamera
extends Node3D

# Kipengele #12: Kamera ya Kisanii
# Procedural camera for cinematic scene direction
# Switches between close-up and wide shots based on scene context
# Can be attached to main scene as a child Node3D, or used independently

@export_group("Camera Settings")
@export var target_node: Node3D = null
@export var shot_distance: float = 10.0
@export var close_up_distance: float = 3.0
@export var wide_distance: float = 15.0
@export var transition_speed: float = 5.0

@export_group("Shot Types")
@export var current_shot: int = 0  # 0=wide, 1=close-up
@export var shot_timer: float = 0.0
@export var shot_duration: float = 5.0


func _ready() -> void:
	shot_timer = shot_duration


func _physics_process(delta: float) -> void:
	shot_timer -= delta
	if shot_timer <= 0.0:
		current_shot = (current_shot + 1) % 2
		if current_shot == 0:
			shot_distance = lerpf(shot_distance, wide_distance, 0.1)
		else:
			shot_distance = lerpf(shot_distance, close_up_distance, 0.1)
		shot_timer = shot_duration


func set_target(node: Node3D) -> void:
	target_node = node


func switch_to_closeup() -> void:
	current_shot = 1
	shot_timer = 0.0


func switch_to_wide() -> void:
	current_shot = 0
	shot_timer = 0.0


func _process(_delta: float) -> void:
	if target_node != null and target_node.is_inside_tree():
		if current_shot == 0:
			# Wide shot - keep distance, overview
			global_position = target_node.global_position + Vector3(0, 2, -shot_distance)
		else:
			# Close-up - focus on character
			global_position = target_node.global_position + Vector3(0, 1.5, -close_up_distance)

		# Look at target (handle both 3D and 2D targets)
		var target_pos: Vector3 = target_node.global_position
		if target_node is Camera3D:
			# Camera target - lead the camera slightly in target view direction
			var forward: Vector3 = -target_node.global_transform.basis.z
			look_at(target_pos + forward * 2.0 + Vector3(0, 1, 0))
		else:
			look_at(target_pos + Vector3(0, 1, 0))