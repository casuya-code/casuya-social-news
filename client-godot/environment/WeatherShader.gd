class_name WeatherShader
extends Node
## Feature #30: Dynamic Weather.
##
## Drives a world-environment shader based on the current weather
## condition. Modulates sky colour, fog density, and particle intensity.
## The shader parameters are set on a WorldEnvironment's sky material
## and environment fog properties.

signal weather_visual_changed(condition: String, intensity: float)

const WEATHER_PRESETS := {
	"angavu": {
		"sky_color": Color(0.4, 0.6, 0.9),
		"cloud_density": 0.1,
		"fog_density": 0.0,
		"sun_energy": 1.0,
		"particle_count": 0,
	},
	"mawingu": {
		"sky_color": Color(0.55, 0.6, 0.7),
		"cloud_density": 0.6,
		"fog_density": 0.02,
		"sun_energy": 0.6,
		"particle_count": 0,
	},
	"mvua": {
		"sky_color": Color(0.35, 0.4, 0.55),
		"cloud_density": 0.8,
		"fog_density": 0.06,
		"sun_energy": 0.3,
		"particle_count": 200,
	},
	"dhoruba": {
		"sky_color": Color(0.2, 0.25, 0.35),
		"cloud_density": 0.95,
		"fog_density": 0.12,
		"sun_energy": 0.15,
		"particle_count": 500,
	},
	"joto": {
		"sky_color": Color(0.8, 0.7, 0.5),
		"cloud_density": 0.05,
		"fog_density": 0.0,
		"sun_energy": 1.2,
		"particle_count": 0,
	},
	"hewa_safi": {
		"sky_color": Color(0.3, 0.55, 0.85),
		"cloud_density": 0.0,
		"fog_density": 0.0,
		"sun_energy": 0.9,
		"particle_count": 0,
	},
}

var _sky_material: ProceduralSkyMaterial
var _environment: Environment
var _current_condition: String = "angavu"
var _transition_speed := 2.0
var _target_preset: Dictionary = {}


func setup(environment: Environment) -> void:
	_environment = environment
	if _environment != null and _environment.sky != null:
		if _environment.sky.sky_material is ProceduralSkyMaterial:
			_sky_material = _environment.sky.sky_material


func set_weather(condition: String) -> void:
	_current_condition = condition
	_target_preset = WEATHER_PRESETS.get(condition, WEATHER_PRESETS["angavu"])
	_apply()


func get_condition() -> String:
	return _current_condition


func _process(delta: float) -> void:
	if _target_preset.is_empty() or _sky_material == null:
		return
	var target_sky: Color = _target_preset.get("sky_color", Color.WHITE)
	_sky_material.sky_top_color = _sky_material.sky_top_color.lerp(target_sky, delta * _transition_speed)
	_sky_material.sky_horizon_color = _sky_material.sky_horizon_color.lerp(target_sky.lightened(0.2), delta * _transition_speed)


func _apply() -> void:
	if _target_preset.is_empty():
		return
	var fog_density: float = _target_preset.get("fog_density", 0.0)
	var sun_energy: float = _target_preset.get("sun_energy", 1.0)
	if _environment != null:
		_environment.fog_density = fog_density
		_environment.volumetric_fog_density = fog_density * 0.5
	weather_visual_changed.emit(_current_condition, sun_energy)
