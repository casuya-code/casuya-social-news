class_name CulturalGesture
extends Node
## Feature #20: African Gestures.
##
## Cultural gesture library — maps emotion/conversation contexts to
## culturally appropriate body gestures (e.g., hand-on-chest greeting,
## open-palm emphasis, head-shake disagreement). Gestures are played as
## procedural animations by scaling/rotating limb nodes.

const GESTURES := {
	"welcome": {
		"hand_right": {"rotation": Vector3(0, 0, -0.5), "duration": 1.2},
		"nod": {"rotation": Vector3(-0.3, 0, 0), "duration": 0.8},
	},
	"emphasis": {
		"hand_right": {"rotation": Vector3(0.5, 0, -0.3), "duration": 0.5},
		"lean_forward": {"rotation": Vector3(-0.1, 0, 0), "duration": 0.6},
	},
	"disagreement": {
		"head_shake": {"rotation": Vector3(0, 0.4, 0), "duration": 1.0, "repeats": 3},
	},
	"praise": {
		"hand_left": {"rotation": Vector3(0, 0, 0.3), "duration": 0.8},
		"lean_back": {"rotation": Vector3(0.1, 0, 0), "duration": 0.8},
	},
	"mourning": {
		"head_bow": {"rotation": Vector3(0.4, 0, 0), "duration": 2.0},
		"hand_right": {"rotation": Vector3(-0.3, 0, 0.2), "duration": 2.0},
	},
}

var _character_id: String
var _nodes: Dictionary = {}
var _current_gesture: String = ""
var _gesture_timer := 0.0
var _gesture_duration := 0.0
var _rest_positions: Dictionary = {}


func setup(character_id: String, nodes: Dictionary) -> void:
	_character_id = character_id
	_nodes = nodes
	for key: String in _nodes:
		var node: Node3D = _nodes[key]
		if node != null:
			_rest_positions[key] = node.rotation


func play_gesture(gesture_name: String) -> void:
	if not GESTURES.has(gesture_name):
		return
	_current_gesture = gesture_name
	_gesture_timer = 0.0
	var gesture: Dictionary = GESTURES[gesture_name]
	_gesture_duration = 0.0
	for key: String in gesture:
		var dur: float = gesture[key].get("duration", 1.0)
		if dur > _gesture_duration:
			_gesture_duration = dur


func stop() -> void:
	_current_gesture = ""
	_apply_rest()


func get_available_gestures() -> Array:
	return GESTURES.keys()


func _process(delta: float) -> void:
	if _current_gesture == "":
		return
	_gesture_timer += delta
	if _gesture_timer >= _gesture_duration:
		_apply_rest()
		_current_gesture = ""
		return
	var gesture: Dictionary = GESTURES[_current_gesture]
	var progress := _gesture_timer / _gesture_duration
	var ease := sin(progress * PI)  # smooth rise and fall
	for key: String in gesture:
		if not _nodes.has(key):
			continue
		var node: Node3D = _nodes[key]
		if node == null:
			continue
		var target_rot: Vector3 = gesture[key].get("rotation", Vector3.ZERO)
		var repeats: int = gesture[key].get("repeats", 1)
		var wave := sin(progress * PI * repeats)
		node.rotation = _rest_positions.get(key, Vector3.ZERO) + target_rot * ease * wave


func _apply_rest() -> void:
	for key: String in _nodes:
		var node: Node3D = _nodes[key]
		if node != null and _rest_positions.has(key):
			node.rotation = _rest_positions[key]
