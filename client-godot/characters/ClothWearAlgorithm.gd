class_name ClothWearAlgorithm
extends Node
## Feature #28: Aging Clothing (Mavazi Yanayozeeka).
##
## Simulates clothes aging/wearing over the course of a story. Drives
## shader parameters on the character's clothing material: dirt overlay,
## colour fade, wrinkle intensity. Increases progressively as the story
## reaches its climax, giving visual weight to the drama's progression.

signal cloth_wear_changed(character_id: String, wear: float)

const MAX_WEAR := 1.0
const WEAR_RATE := 0.05

var _character_id: String
var _clothing_material: Material
var _wear := 0.0
var _active := false


func setup(character_id: String, material: Material) -> void:
	_character_id = character_id
	_clothing_material = material


func set_active(active: bool) -> void:
	_active = active


func reset_wear() -> void:
	_wear = 0.0
	_apply_wear()
	cloth_wear_changed.emit(_character_id, 0.0)


func add_wear(amount: float) -> void:
	_wear = clampf(_wear + amount, 0.0, MAX_WEAR)
	_apply_wear()
	cloth_wear_changed.emit(_character_id, _wear)


func set_wear(value: float) -> void:
	_wear = clampf(value, 0.0, MAX_WEAR)
	_apply_wear()
	cloth_wear_changed.emit(_character_id, _wear)


func get_wear() -> float:
	return _wear


func _process(delta: float) -> void:
	if not _active:
		return
	add_wear(WEAR_RATE * delta)


func _apply_wear() -> void:
	if _clothing_material == null:
		return
	var fade := 1.0 - _wear * 0.3
	if _clothing_material is StandardMaterial3D:
		_clothing_material.albedo_color = Color(fade, fade, fade, 1.0)
	elif _clothing_material is ShaderMaterial:
		if _clothing_material.has_shader_parameter("dirt"):
			_clothing_material.set_shader_parameter("dirt", _wear)
		if _clothing_material.has_shader_parameter("wrinkle"):
			_clothing_material.set_shader_parameter("wrinkle", _wear * 0.8)
		if _clothing_material.has_shader_parameter("albedo_fade"):
			_clothing_material.set_shader_parameter("albedo_fade", fade)
