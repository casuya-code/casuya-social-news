class_name ProximityShader
extends Node
## Feature #21: Dynamic Proximity (2D).
##
## Modulates character appearance based on distance from the camera/listener.
## Closer characters are brighter; distant characters fade slightly.

const NEAR_DISTANCE := 60.0
const FAR_DISTANCE := 400.0
const MIN_BRIGHTNESS := 0.5
const MAX_BRIGHTNESS := 1.0

var _camera: Node2D
var _character_nodes: Array[CanvasItem] = []
var _character_id: String
var _enabled := true


func setup(character_id: String, camera: Node2D) -> void:
	_character_id = character_id
	_camera = camera


func register_mesh(node: CanvasItem) -> void:
	if node not in _character_nodes:
		_character_nodes.append(node)


func set_enabled(enabled: bool) -> void:
	_enabled = enabled


func _process(_delta: float) -> void:
	if not _enabled or _camera == null:
		return
	for node in _character_nodes:
		if node == null or not is_instance_valid(node):
			continue
		var distance := _camera.global_position.distance_to(node.global_position)
		var factor := clampf((distance - NEAR_DISTANCE) / (FAR_DISTANCE - NEAR_DISTANCE), 0.0, 1.0)
		var brightness := lerpf(MAX_BRIGHTNESS, MIN_BRIGHTNESS, factor)
		node.modulate = Color(brightness, brightness, brightness, node.modulate.a)
