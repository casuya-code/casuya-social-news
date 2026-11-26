class_name TextureSwapper
extends Node
## Feature #23: Dynamic Texture Swapping (2D).
##
## Swaps character textures based on mood, weather, or time of day.

signal texture_swapped(character_id: String, texture_name: String)

var _character_id: String
var _node: CanvasItem
var _texture_sets: Dictionary = {}  # name -> {day: Texture2D, night: Texture2D}
var _current_name: String = ""
var _current_period: String = "mchana"


func setup(character_id: String, node: CanvasItem) -> void:
	_character_id = character_id
	_node = node


## Register a named texture variant with day/night versions.
func register_texture(name: String, day_tex: Texture2D, night_tex: Texture2D) -> void:
	_texture_sets[name] = {"day": day_tex, "night": night_tex}


func swap(texture_name: String) -> void:
	if not _texture_sets.has(texture_name):
		return
	var tex_set: Dictionary = _texture_sets[texture_name]
	var period := _time_period()
	var tex: Texture2D = tex_set.get(period, tex_set.get("day"))
	if _node != null and "texture" in _node:
		_node.texture = tex
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
