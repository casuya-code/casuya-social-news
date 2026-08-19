class_name ProximityShader
extends Node
## Feature #21: Dynamic Proximity.
##
## Modulates character appearance based on their distance from the camera
## or the listener. Closer characters get more detail (brighter, sharper),
## distant characters fade slightly. Also used for scene depth — characters
## in the background are dimmer. Drives a ShaderMaterial on the character
## mesh if available.

const NEAR_DISTANCE := 3.0
const FAR_DISTANCE := 15.0
const MIN_BRIGHTNESS := 0.5
const MAX_BRIGHTNESS := 1.0
const MIN_SATURATION := 0.6
const MAX_SATURATION := 1.0

var _camera: Camera3D
var _character_meshes: Array[MeshInstance3D] = []
var _character_id: String
var _enabled := true


func setup(character_id: String, camera: Camera3D) -> void:
	_character_id = character_id
	_camera = camera


func register_mesh(mesh: MeshInstance3D) -> void:
	if mesh not in _character_meshes:
		_character_meshes.append(mesh)


func set_enabled(enabled: bool) -> void:
	_enabled = enabled


func _process(_delta: float) -> void:
	if not _enabled or _camera == null:
		return
	for mesh in _character_meshes:
		if mesh == null:
			continue
		var distance := _camera.global_position.distance_to(mesh.global_position)
		var factor := clampf((distance - NEAR_DISTANCE) / (FAR_DISTANCE - NEAR_DISTANCE), 0.0, 1.0)
		var brightness := lerpf(MAX_BRIGHTNESS, MIN_BRIGHTNESS, factor)
		var saturation := lerpf(MAX_SATURATION, MIN_SATURATION, factor)
		var mat: Material = mesh.get_surface_override_material(0)
		if mat is ShaderMaterial:
			if mat.has_shader_parameter("brightness"):
				mat.set_shader_parameter("brightness", brightness)
			if mat.has_shader_parameter("saturation"):
				mat.set_shader_parameter("saturation", saturation)
		elif mat is StandardMaterial3D:
			mat.albedo_color = Color(brightness, brightness, brightness, 1.0)
