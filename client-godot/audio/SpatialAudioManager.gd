class_name SpatialAudioManager
extends Node
## Feature #32: Spatial Procedural Audio.
##
## Positions each character in the stereo field with a procedural pan so the
## radio drama has a real sense of place — characters talk over each other
## from distinct positions. Pan is derived deterministically from the
## character id (stable per character), then applied to the active player.

signal pan_changed(character_id: String, pan: float)

## Discrete stereo slots — keeps voices well separated and predictable.
const PAN_SLOTS := [-0.8, -0.4, 0.0, 0.4, 0.8]

## World-space spread (metres) the pan maps onto for the 3D listener.
const PAN_SPREAD := 3.0

var _positions: Dictionary = {}  # character_id -> float pan


## Compute the deterministic pan slot for a character id (range -1..1).
func procedural_pan(character_id: String) -> float:
	var hash_val: int = abs(int(character_id.hash()))
	var slot := hash_val % PAN_SLOTS.size()
	return PAN_SLOTS[slot]


## Pan a 3D audio player for the given character. Returns the pan applied.
func apply_to(player: AudioStreamPlayer3D, character_id: String) -> float:
	var pan := procedural_pan(character_id)
	player.position = Vector3(pan * PAN_SPREAD, 0.0, 0.0)
	player.panning_strength = 1.0
	_positions[character_id] = pan
	pan_changed.emit(character_id, pan)
	return pan


func pan_for(character_id: String) -> float:
	if _positions.has(character_id):
		return _positions[character_id]
	return procedural_pan(character_id)