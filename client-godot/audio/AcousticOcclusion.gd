class_name AcousticOcclusion
extends Node
## Feature #33: Acoustic Occlusion ("Mwangwi wa Sauti").
##
## Models the acoustics of a line's delivery: calm/whispered and distant
## deliveries are attenuated and echoed, while shouting/close lines stay
## bright and loud. A single occlusion factor (0..1) drives gain and pitch
## on the active player.

signal occlusion_changed(character_id: String, factor: float)

const MAX_ATTEN_DB := -14.0
const MAX_PITCH_DROP := 0.15
## Feature #30: weather mood bias (from GET /weather mood_offset, in [-1, 1])
## shifts the room's base acoustics — stormy skies darken, bright skies lift.
const MAX_WEATHER_DB := 3.0
const MAX_WEATHER_PITCH := 0.05

var _factors: Dictionary = {}  # character_id -> factor
var _weather_bias := 0.0


## Map an emotion tag to an occlusion factor (0 = clear/bright, 1 = muffled).
func factor_for_emotion(emotion: String) -> float:
	match emotion:
		"anapiga_kelele", "anakasirika", "anashangaa":
			return 0.0
		"anafikiria", "anahofia", "anaomba_msaada":
			return 0.8
		"anaongea_kwa_utulivu", "anajigamba", "anadhihaki":
			return 0.35
		"anaongea_kwa_huzuni", "anasikitika":
			return 0.55
		_:
			return 0.2


## Volume attenuation in dB for a given occlusion factor.
func attenuation_db(factor: float) -> float:
	return MAX_ATTEN_DB * clampf(factor, 0.0, 1.0)


## Pitch multiplier for a given occlusion factor (muffled = slightly lower).
func pitch_scale(factor: float) -> float:
	return 1.0 - MAX_PITCH_DROP * clampf(factor, 0.0, 1.0)


## Set the weather mood bias ([-1, 1]) from the /weather mood_offset. A
## negative bias (dhoruba) darkens the room, a positive one brightens it.
func set_weather_bias(bias: float) -> void:
	_weather_bias = clampf(bias, -1.0, 1.0)


func weather_bias() -> float:
	return _weather_bias


## Apply occlusion acoustics to an audio player for a character. Returns the
## applied factor.
func apply_to(player: AudioStreamPlayer, character_id: String, emotion: String) -> float:
	var factor := factor_for_emotion(emotion)
	player.volume_db = attenuation_db(factor) + _weather_bias * MAX_WEATHER_DB
	player.pitch_scale = pitch_scale(factor) + _weather_bias * MAX_WEATHER_PITCH
	_factors[character_id] = factor
	occlusion_changed.emit(character_id, factor)
	return factor


func factor_for(character_id: String) -> float:
	return _factors.get(character_id, 0.0)
