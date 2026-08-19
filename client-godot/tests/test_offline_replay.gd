extends SceneTree
## Headless test for Offline Replay:
## Verifies that cached scripts with cached audio bytes load directly from OfflineCache
## and trigger playback without requiring network connectivity.

const CACHE_SCRIPT := preload("res://storage/OfflineCache.gd")
const DRAMA_SCRIPT := preload("res://audio/OverlapSpeechPlayer.gd")

var _cache: OfflineCache
var _drama: OverlapSpeechPlayer
var _audio_lines_loaded := 0
var _test_script_id := "test_story_offline_001"
var _started_lines: Array[int] = []


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	_cache = CACHE_SCRIPT.new()
	_cache.cache_dir = "user://test_offline_replay_cache"
	root.add_child(_cache)
	_cache.clear()

	var wav_bytes := _create_test_wav_bytes(0.5)

	# Store script in cache
	var mock_script := {
		"script_id": _test_script_id,
		"headline": "Habari za Majaribio Nje ya Mtandao",
		"lines": [
			{"index": 0, "character_id": "char_mjomba", "text": "Jambo la kwanza", "overlap": false},
			{"index": 1, "character_id": "char_shangazi", "text": "Jambo la pili", "overlap": false}
		]
	}

	if not _cache.cache_script(mock_script):
		_fail("Failed to cache script in OfflineCache")
		return

	if not _cache.cache_audio(_test_script_id, 0, wav_bytes):
		_fail("Failed to cache line 0 audio")
		return

	if not _cache.cache_audio(_test_script_id, 1, wav_bytes):
		_fail("Failed to cache line 1 audio")
		return

	# Verify manifest contains the script
	if not _cache.has(_test_script_id):
		_fail("Cache missing test script id")
		return

	# Simulate offline loading pipeline
	var loaded_script := _cache.load_script(_test_script_id)
	if loaded_script.is_empty():
		_fail("load_script returned empty")
		return

	var lines: Array = loaded_script.get("lines", [])
	var audio_map: Dictionary = {}
	for i in range(lines.size()):
		var audio_bytes := _cache.load_audio(_test_script_id, i)
		if audio_bytes.is_empty():
			_fail("load_audio returned empty bytes for line %d" % i)
			return
		var stream := AudioStreamWAV.new()
		var loaded: AudioStreamWAV = stream.load_from_buffer(audio_bytes)
		if loaded == null:
			# Fallback for raw PCM bytes
			stream.format = AudioStreamWAV.FORMAT_16_BITS
			stream.mix_rate = 8000
			stream.data = audio_bytes
			loaded = stream
		audio_map[i] = loaded
		_audio_lines_loaded += 1

	if _audio_lines_loaded != lines.size():
		_fail("Loaded line count mismatch: expected %d, got %d" % [lines.size(), _audio_lines_loaded])
		return

	# Wire and play on OverlapSpeechPlayer
	_drama = DRAMA_SCRIPT.new()
	root.add_child(_drama)
	_drama.line_started.connect(func(idx: int) -> void:
		_started_lines.append(idx)
	)

	_drama.play(lines, audio_map)
	await create_timer(1.2).timeout
	_drama.stop()

	if _started_lines.size() < 1:
		_fail("Drama player failed to start with cached audio")
		return

	_cache.clear()
	print("[TEST] PASS — offline replay audio successfully cached, loaded from disk, and played (lines started: %s)" % str(_started_lines))
	quit(0)


func _create_test_wav_bytes(seconds: float) -> PackedByteArray:
	var bytes := PackedByteArray()
	var sample_rate := 8000
	var samples := int(seconds * float(sample_rate))
	var data_size := samples * 2
	var total_size := 36 + data_size

	bytes.append_array("RIFF".to_utf8_buffer())
	bytes.append(total_size & 0xFF)
	bytes.append((total_size >> 8) & 0xFF)
	bytes.append((total_size >> 16) & 0xFF)
	bytes.append((total_size >> 24) & 0xFF)
	bytes.append_array("WAVEfmt ".to_utf8_buffer())
	bytes.append_array([16, 0, 0, 0])  # Subchunk1Size
	bytes.append_array([1, 0])          # AudioFormat (PCM = 1)
	bytes.append_array([1, 0])          # NumChannels (Mono = 1)
	bytes.append(sample_rate & 0xFF)
	bytes.append((sample_rate >> 8) & 0xFF)
	bytes.append((sample_rate >> 16) & 0xFF)
	bytes.append((sample_rate >> 24) & 0xFF)
	var byte_rate := sample_rate * 2
	bytes.append(byte_rate & 0xFF)
	bytes.append((byte_rate >> 8) & 0xFF)
	bytes.append((byte_rate >> 16) & 0xFF)
	bytes.append((byte_rate >> 24) & 0xFF)
	bytes.append_array([2, 0])          # BlockAlign (2 bytes)
	bytes.append_array([16, 0])         # BitsPerSample (16 bits)
	bytes.append_array("data".to_utf8_buffer())
	bytes.append(data_size & 0xFF)
	bytes.append((data_size >> 8) & 0xFF)
	bytes.append((data_size >> 16) & 0xFF)
	bytes.append((data_size >> 24) & 0xFF)
	for _i in range(data_size):
		bytes.append(0)
	return bytes


func _fail(msg: String) -> void:
	print("[TEST] FAIL — ", msg)
	quit(1)
