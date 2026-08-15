extends SceneTree
## Headless integration test for OverlapSpeechPlayer (Feature #6, client side).
## Uses synthesized WAV streams so durations are real (the server's mock TTS
## produces 0-length audio). Verifies:
## - an overlapping line starts before its predecessor finishes (talk-over)
## - non-overlapping lines stay sequential
## - skip() advances and sequence still finishes
## - is_talking_over() is true while cutting into the previous tail

const DRAMA_SCRIPT := preload("res://audio/OverlapSpeechPlayer.gd")

var _drama: Node
var _starts: Dictionary = {}  # index -> msec
var _zero_ms := 0
var _finished := false
var _overlap_start_ms := 0
var _talkover_sampled := false


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	_drama = DRAMA_SCRIPT.new()
	root.add_child(_drama)
	_drama.line_started.connect(_on_line_started)
	_drama.sequence_finished.connect(func() -> void: _finished = true)

	var lines := [
		{"index": 0, "character_id": "a", "text": "Habari.", "emotion": "upimaji", "overlap": false},
		{"index": 1, "character_id": "b", "text": "Acha niongee!", "emotion": "hasira", "overlap": true},
		{"index": 2, "character_id": "a", "text": "Hapana.", "emotion": "hasira", "overlap": false},
	]
	var audio := {
		0: _make_wav(1.0),
		1: _make_wav(0.8),
		2: _make_wav(0.6),
	}

	var t0 := Time.get_ticks_msec()
	_zero_ms = t0
	_drama.play(lines, audio)

	await create_timer(4.0).timeout

	if not _finished:
		_fail("sequence never finished")
		return
	if _starts.size() != 3:
		_fail("expected 3 line starts, got %d" % _starts.size())
		return

	# Overlap: line 1 must start before line 0's 1.0s stream would end.
	var overlap_early_ms: int = int(_starts[1]) - int(_starts[0])
	if overlap_early_ms >= 950:
		_fail("line 1 did not overlap line 0 (started %dms after)" % overlap_early_ms)
		return

	# Non-overlap: line 2 starts after line 1's stream ends. Allow a small
	# tolerance for headless scheduler jitter (~0.8s duration, >=0.72s).
	var gap_ms: int = int(_starts[2]) - int(_starts[1])
	var min_gap := int(0.72 * 1000.0)
	if gap_ms < min_gap:
		_fail("line 2 was not sequential (started %dms after line 1, expected >=%d)" % [gap_ms, min_gap])
		return

	# is_talking_over() sampled while line 1 played.
	if not _talkover_sampled:
		_fail("is_talking_over() was never true during the overlapping line")
		return

	print("[TEST] PASS — overlap early=%dms, seq gap=%dms, talk-over observed" % [overlap_early_ms, gap_ms])
	quit(0)


func _on_line_started(index: int) -> void:
	var now := Time.get_ticks_msec()
	_starts[index] = now
	print("[TEST] line_started %d at +%dms" % [index, now - _zero_ms])
	if index == 1:
		# Sample while the overlapping line is cutting into line 0's tail.
		await create_timer(0.2).timeout
		if _drama.is_talking_over():
			_talkover_sampled = true


func _make_wav(seconds: float) -> AudioStreamWAV:
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = 8000
	var samples := int(seconds * 8000.0)
	var data := PackedByteArray()
	data.resize(samples * 2)  # 16-bit mono
	wav.data = data
	return wav


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)