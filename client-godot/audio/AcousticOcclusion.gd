class_name AcousticOcclusion
extends Node
## Feature #33: Acoustic Occlusion ("Mwangwi wa Sauti").
##
## Models the acoustics of a line's delivery: calm/whispered and distant
## deliveries are attenuated and echoed, while shouting/close lines stay
## bright and loud. A single occlusion factor (0..1) drives gain, pitch and
## echo send on the active player.

signal occlusion_changed(character_id: String, factor: float)

const MAX_ATTEN_DB := -14.0
const MAX_PITCH_DROP := 0.15
const MAX_ECHO := 0.7

var _factors: Dictionary = {}  # character_id -> factor


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


## Echo send amount (0..1) for a given occlusion factor.
func echo_amount(factor: float) -> float:
	return MAX_ECHO * clampf(factor, 0.0, 1.0)


## Apply occlusion acoustics to a 3D audio player for a character. Returns the
## applied factor.
func apply_to(player: AudioStreamPlayer3D, character_id: String, emotion: String) -> float:
	var factor := factor_for_emotion(emotion)
	player.volume_db = attenuation_db(factor)
	player.pitch_scale = pitch_scale(factor)
	_factors[character_id] = factor
	occlusion_changed.emit(character_id, factor)
	return factor


func factor_for(character_id: String) -> float:
	return _factors.get(character_id, 0.0)