extends SceneTree
## Headless test for LipsyncController and PhonemeAnalyzer:
## Verifies signal emissions, phoneme-to-shape mapping, amplitude thresholds,
## and energy classifications.

const LIPSYNC_SCRIPT := preload("res://facial/LipsyncController.gd")
const PHONEME_SCRIPT := preload("res://facial/PhonemeAnalyzer.gd")

var _emitted_signals: Array[Dictionary] = []


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	var lipsync: Node = LIPSYNC_SCRIPT.new()
	root.add_child(lipsync)
	lipsync.setup("char_mjomba", null)
	lipsync.mouth_changed.connect(_on_mouth_changed)

	# Test phoneme mapping directly through update_from_phoneme
	lipsync.update_from_phoneme("X", 0.0)
	if lipsync.get_shape() != 0:
		_fail("Phoneme X should produce shape 0, got %d" % lipsync.get_shape())
		return

	lipsync.update_from_phoneme("P", 0.1)
	if lipsync.get_shape() != 1:
		_fail("Phoneme P should produce shape 1, got %d" % lipsync.get_shape())
		return

	lipsync.update_from_phoneme("I", 0.2)
	if lipsync.get_shape() != 2:
		_fail("Phoneme I should produce shape 2, got %d" % lipsync.get_shape())
		return

	lipsync.update_from_phoneme("E", 0.3)
	if lipsync.get_shape() != 3:
		_fail("Phoneme E should produce shape 3, got %d" % lipsync.get_shape())
		return

	lipsync.update_from_phoneme("A", 0.4)
	if lipsync.get_shape() != 4:
		_fail("Phoneme A should produce shape 4, got %d" % lipsync.get_shape())
		return

	if _emitted_signals.size() < 4:
		_fail("Expected at least 4 mouth_changed signal emissions, got %d" % _emitted_signals.size())
		return

	# Verify signal contents
	var last_sig: Dictionary = _emitted_signals.back()
	if last_sig["char_id"] != "char_mjomba" or last_sig["shape"] != 4:
		_fail("Last signal payload mismatch: %s" % str(last_sig))
		return

	# Test amplitude to shape mappings
	if lipsync._amplitude_to_shape(0.04) != 0:
		_fail("Amplitude 0.04 should be shape 0")
		return
	if lipsync._amplitude_to_shape(0.15) != 1:
		_fail("Amplitude 0.15 should be shape 1")
		return
	if lipsync._amplitude_to_shape(0.35) != 2:
		_fail("Amplitude 0.35 should be shape 2")
		return
	if lipsync._amplitude_to_shape(0.55) != 3:
		_fail("Amplitude 0.55 should be shape 3")
		return
	if lipsync._amplitude_to_shape(0.85) != 4:
		_fail("Amplitude 0.85 should be shape 4")
		return

	# Test PhonemeAnalyzer energy classifications
	var analyzer: RefCounted = PHONEME_SCRIPT.new()
	if analyzer._classify_energy(0.02) != "silence":
		_fail("Energy 0.02 should classify as silence")
		return
	if analyzer._classify_energy(0.10) != "consonant_fricative":
		_fail("Energy 0.10 should classify as consonant_fricative")
		return
	if analyzer._classify_energy(0.25) != "vowel_close":
		_fail("Energy 0.25 should classify as vowel_close")
		return
	if analyzer._classify_energy(0.45) != "vowel_mid":
		_fail("Energy 0.45 should classify as vowel_mid")
		return
	if analyzer._classify_energy(0.65) != "vowel_open":
		_fail("Energy 0.65 should classify as vowel_open")
		return
	if analyzer._classify_energy(0.90) != "consonant_plosive":
		_fail("Energy 0.90 should classify as consonant_plosive")
		return

	print("[TEST] PASS — lipsync controller signal emissions, amplitude mapping, and phoneme analyzer valid")
	quit(0)


func _on_mouth_changed(character_id: String, shape: int) -> void:
	_emitted_signals.append({"char_id": character_id, "shape": shape})


func _fail(msg: String) -> void:
	print("[TEST] FAIL — ", msg)
	quit(1)
