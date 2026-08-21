class_name SpatialAudioManager
extends Node
## Feature #32: Spatial Procedural Audio.
##
## Positions each character in the stereo field with a procedural pan so the
## radio drama has a real sense of place — characters talk over each other
## from distinct positions. Pan is derived deterministically from the
## character id, then applied via Audio bus panning.

signal pan_changed(character_id: String, pan: float)

## Discrete stereo slots — keeps voices well separated and predictable.
const PAN_SLOTS := [-0.8, -0.4, 0.0, 0.4, 0.8]

var _positions: Dictionary = {}  # character_id -> float pan


## Compute the deterministic pan slot for a character id (range -1..1).
func procedural_pan(character_id: String) -> float:
	var hash_val: int = abs(int(character_id.hash()))
	var slot := hash_val % PAN_SLOTS.size()
	return PAN_SLOTS[slot]


## Pan an audio player for the given character via volume balance. Returns the pan applied.
func apply_to(player: AudioStreamPlayer, character_id: String) -> float:
	var pan := procedural_pan(character_id)
	# Apply pan via volume: -1.0 = full left, 0.0 = center, 1.0 = full right
	# Convert pan to a volume multiplier for stereo balance
	var vol_left := 1.0 - maxf(pan, 0.0)
	var vol_right := 1.0 + minf(pan, 0.0)
	# Use volume_db to apply balance
	player.volume_db = -absf(pan) * 6.0  # attenuate off-center voices slightly
	_positions[character_id] = pan
	pan_changed.emit(character_id, pan)
	return pan


func pan_for(character_id: String) -> float:
	if _positions.has(character_id):
		return _positions[character_id]
	return procedural_pan(character_id)
