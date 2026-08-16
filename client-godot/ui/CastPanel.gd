extends VBoxContainer
## Live cast status panel (Feature #27). Renders the current on-air cast:
## name, mood, and the memory line they're carrying, fed from three sources:
##   - ws_state_snapshot: {char_id: {mood: float, memory: str}}
##   - script_delta characters_delta: [{id, name, mood, mood_label, memory}]
##   - loaded scripts: characters[{id, name, mood_value, memory}]
##
## Single responsibility: cast state -> sorted list of human-readable lines.

const MOOD_LOW := -0.5
const MOOD_MID := -0.15
const MOOD_HIGH := 0.15

var _states: Dictionary = {}  # char_id -> {mood: float, memory: str}
var _names: Dictionary = {}   # char_id -> display name


## Replace the whole cast from a ws state_snapshot payload.
func set_snapshot(characters: Dictionary) -> void:
	_states.clear()
	for char_id: String in characters:
		var state: Dictionary = characters[char_id]
		_states[char_id] = {
			"mood": float(state.get("mood", 0.0)),
			"memory": str(state.get("memory", "")),
		}
	_rebuild()


## Merge per-character changes from a script_delta characters_delta list.
func apply_deltas(deltas: Array) -> void:
	for entry in deltas:
		if not entry is Dictionary:
			continue
		var char_id := str(entry.get("id", ""))
		if char_id == "":
			continue
		var name := str(entry.get("name", ""))
		if name != "":
			_names[char_id] = name
		var state: Dictionary = _states.get(char_id, {"mood": 0.0, "memory": ""})
		if entry.has("mood"):
			state["mood"] = float(entry["mood"])
		if entry.has("memory"):
			state["memory"] = str(entry["memory"])
		_states[char_id] = state
	_rebuild()


## Register characters (id -> name, mood, memory) from a loaded script so the
## panel can display names even before a delta carries them.
func register_script(script: Dictionary) -> void:
	for character in script.get("characters", []):
		if not character is Dictionary:
			continue
		var char_id := str(character.get("id", ""))
		if char_id == "":
			continue
		_names[char_id] = str(character.get("name", char_id))
		var state: Dictionary = _states.get(char_id, {"mood": 0.0, "memory": ""})
		state["mood"] = float(character.get("mood_value", state.get("mood", 0.0)))
		state["memory"] = str(character.get("memory", state.get("memory", "")))
		_states[char_id] = state
	_rebuild()


## Human-friendly mood label, mirroring the server's nlp/memory mood_label().
func mood_label(mood: float) -> String:
	if mood <= MOOD_LOW:
		return "hana furaha"
	if mood <= MOOD_MID:
		return "ameguswa"
	if mood >= MOOD_HIGH * 3.0:  # 0.5
		return "anafuraha"
	if mood >= MOOD_HIGH:
		return "ana msisimko"
	return "hali ya kawaida"


func cast_count() -> int:
	return _states.size()


## Rebuild the child lines from current state, sorted by display name.
func _rebuild() -> void:
	for child in get_children():
		child.queue_free()
	var ids: Array = _states.keys()
	ids.sort_custom(func(a: String, b: String) -> bool:
		return _display_name(a) < _display_name(b)
	)
	for char_id in ids:
		var state: Dictionary = _states[char_id]
		var mood: float = float(state.get("mood", 0.0))
		var memory := str(state.get("memory", ""))
		var text := "%s — %s" % [_display_name(char_id), mood_label(mood)]
		if memory != "":
			text += ": %s" % memory
		var line := Label.new()
		line.text = text
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		add_child(line)


func _display_name(char_id: String) -> String:
	return str(_names.get(char_id, char_id))