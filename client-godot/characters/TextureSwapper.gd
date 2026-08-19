class_name TextureSwapper
extends Node
## Feature #23: Dynamic Texture Swapping.
##
## Swaps character textures based on mood, weather, or time of day.
## Characters can wear different expressions or clothing colours without
## duplicating models — the texture set is preloaded on setup, and
## `swap()` picks the right variant at runtime.

signal texture_swapped(character_id: String, texture_name: String)

var _character_id: String
var _mesh: MeshInstance3D
var _texture_sets: Dictionary = {}  # name -> {day: Texture2D, night: Texture2D}
var _current_name: String = ""
var _current_period: String = "mchana"


func setup(character_id: String, mesh: MeshInstance3D) -> void:
	_character_id = character_id
	_mesh = mesh


## Register a named texture variant with day/night versions.
func register_texture(name: String, day_tex: Texture2D, night_tex: Texture2D) -> void:
	_texture_sets[name] = {"day": day_tex, "night": night_tex}


func swap(texture_name: String) -> void:
	if not _texture_sets.has(texture_name):
		return
	var set: Dictionary = _texture_sets[texture_name]
	var period := _time_period()
	var tex: Texture2D = set.get(period, set.get("day"))
	if _mesh != null and _mesh.get_surface_override_material(0) != null:
		var mat: StandardMaterial3D = _mesh.get_surface_override_material(0)
		mat.albedo_texture = tex
	_current_name = texture_name
	texture_swapped.emit(_character_id, texture_name)


func set_time_period(period: String) -> void:
	_current_period = period
	if _current_name != "":
		swap(_current_name)


func get_current() -> String:
	return _current_name


func get_available() -> Array:
	return _texture_sets.keys()


func _time_period() -> String:
	if _current_period != "":
		return _current_period
	return "mchana"
