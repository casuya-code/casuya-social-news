extends SceneTree
## Headless integration test for the live cast panel (ui/CastPanel.gd).
## Verifies:
## - set_snapshot() renders each cast member's name, mood label, memory
## - mood_label() thresholds mirror the server's nlp/memory.mood_label
## - apply_deltas() merges per-character changes from a script_delta
## - register_script() learns names/mood/memory from a loaded script
## - lines are sorted by display name

const CAST_SCRIPT := preload("res://ui/CastPanel.gd")

var _panel: VBoxContainer


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	_panel = CAST_SCRIPT.new()
	root.add_child(_panel)

	# --- mood_label thresholds (mirror server) ---
	if _panel.mood_label(-0.6) != "hana furaha":
		_fail("mood_label(-0.6) should be 'hana furaha'")
		return
	if _panel.mood_label(-0.2) != "ameguswa":
		_fail("mood_label(-0.2) should be 'ameguswa'")
		return
	if _panel.mood_label(0.0) != "hali ya kawaida":
		_fail("mood_label(0.0) should be 'hali ya kawaida'")
		return
	if _panel.mood_label(0.3) != "ana msisimko":
		_fail("mood_label(0.3) should be 'ana msisimko'")
		return
	if _panel.mood_label(0.6) != "anafuraha":
		_fail("mood_label(0.6) should be 'anafuraha'")
		return

	# --- snapshot render ---
	_panel.set_snapshot({
		"char_mjomba": {"mood": -0.6, "memory": "Mechi ya leo"},
		"char_bibi_mkwe": {"mood": 0.6, "memory": ""},
	})
	if _panel.cast_count() != 2:
		_fail("snapshot should register 2 cast members")
		return
	await process_frame
	var lines: Array[Node] = _panel.get_children()
	if lines.size() != 2:
		_fail("snapshot should render 2 lines, got %d" % lines.size())
		return
	# Sorted by name: char_bibi_mkwe before char_mjomba.
	var first: String = (lines[0] as Label).text
	var second: String = (lines[1] as Label).text
	if not first.contains("anafuraha"):
		_fail("bibi should be anafuraha, got: %s" % first)
		return
	if not second.contains("hana furaha") or not second.contains("Mechi ya leo"):
		_fail("mjomba should carry low mood + memory, got: %s" % second)
		return

	# --- deltas merge ---
	_panel.apply_deltas([
		{"id": "char_mjomba", "name": "Mjomba Juma", "mood": 0.2, "memory": ""},
		{"id": "char_rafiki", "name": "Rafiki Neema", "mood": 0.8, "memory": "Ajira mpya"},
	])
	await process_frame
	if _panel.cast_count() != 3:
		_fail("delta should add the new character, count=%d" % _panel.cast_count())
		return
	var found_neema := false
	var found_juma_mood := false
	for child in _panel.get_children():
		var text: String = (child as Label).text
		if text.contains("Rafiki Neema") and text.contains("anafuraha"):
			found_neema = true
		if text.contains("Mjomba Juma") and text.contains("ana msisimko"):
			found_juma_mood = true
	if not found_neema:
		_fail("delta-added character not rendered with mood")
		return
	if not found_juma_mood:
		_fail("delta should update existing character's mood/name")
		return

	# --- register_script learns names + mood_value ---
	_panel.register_script({
		"characters": [
			{"id": "char_rafiki", "name": "Rafiki Neema", "mood_value": -0.5, "memory": "Kumbukumbu"},
		],
	})
	await process_frame
	var rafiki_line := ""
	for child in _panel.get_children():
		var text: String = (child as Label).text
		if text.begins_with("Rafiki Neema"):
			rafiki_line = text
	if not rafiki_line.contains("hana furaha") or not rafiki_line.contains("Kumbukumbu"):
		_fail("register_script should update mood + memory, got: %s" % rafiki_line)
		return

	print("[TEST] PASS — cast panel snapshot, deltas, script registration, mood labels")
	quit(0)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)