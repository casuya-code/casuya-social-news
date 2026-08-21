class_name LightBaker
extends Node
## Feature #29: Stylized Visual Baking.
##
## Procedurally generates stylised lighting/shadow data for scene
## environments based on time of day and weather. Drives OmniLight3D
## or DirectionalLight3D nodes to produce atmospheric, hand-painted
## looking lighting without pre-baked lightmaps.

signal light_updated(light_type: String, color: Color, energy: float)

const TIME_PRESETS := {
	"asubuhi": {"color": Color(1.0, 0.85, 0.7), "energy": 0.7, "shadow_energy": 0.5},
	"mchana": {"color": Color(1.0, 1.0, 0.95), "energy": 1.0, "shadow_energy": 0.8},
	"usiku": {"color": Color(0.3, 0.35, 0.55), "energy": 0.3, "shadow_energy": 0.2},
}

const WEATHER_MODIFIERS := {
	"angavu": {"color_shift": Color(1.0, 1.0, 1.0), "energy_mult": 1.0},
	"mawingu": {"color_shift": Color(0.9, 0.92, 1.0), "energy_mult": 0.75},
	"mvua": {"color_shift": Color(0.75, 0.8, 0.9), "energy_mult": 0.5},
	"dhoruba": {"color_shift": Color(0.5, 0.55, 0.7), "energy_mult": 0.35},
	"joto": {"color_shift": Color(1.0, 0.95, 0.85), "energy_mult": 0.9},
}

var _directional_light: DirectionalLight3D
var _ambient_light: DirectionalLight3D
var _time_of_day: String = "mchana"
var _weather: String = "angavu"
var _mood_offset: float = 0.0


func setup(directional: DirectionalLight3D, ambient: DirectionalLight3D = null) -> void:
	_directional_light = directional
	_ambient_light = ambient


func set_time_of_day(period: String) -> void:
	_time_of_day = period
	_update()


func set_weather(weather_type: String) -> void:
	_weather = weather_type
	_update()


func set_mood_offset(offset: float) -> void:
	_mood_offset = clampf(offset, -1.0, 1.0)
	_update()


func get_time_of_day() -> String:
	return _time_of_day


func get_weather() -> String:
	return _weather


## Computed lighting state (readable by UI / other systems).
var computed_color := Color.WHITE
var computed_energy := 1.0
var computed_shadow_energy := 0.5


func _update() -> void:
	var preset: Dictionary = TIME_PRESETS.get(_time_of_day, TIME_PRESETS["mchana"])
	var weather_mod: Dictionary = WEATHER_MODIFIERS.get(_weather, WEATHER_MODIFIERS["angavu"])
	var base_color: Color = preset["color"]
	var base_energy: float = preset["energy"]
	var color_shift: Color = weather_mod["color_shift"]
	var energy_mult: float = weather_mod["energy_mult"]
	var final_color := base_color * color_shift
	var final_energy := base_energy * energy_mult
	final_energy *= (1.0 + _mood_offset * 0.15)
	computed_color = final_color
	computed_energy = final_energy
	computed_shadow_energy = preset.get("shadow_energy", 0.5) * energy_mult
	if _directional_light != null:
		_directional_light.light_color = final_color
		_directional_light.light_energy = final_energy
		_directional_light.shadow_energy = computed_shadow_energy
	light_updated.emit("directional", final_color, final_energy)
