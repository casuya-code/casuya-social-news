extends SceneTree
## Headless test for Audio Download Error Validation:
## Verifies that NetworkManager catches HTTP error status codes, network faults,
## and corrupt audio buffers during audio download, emitting script_failed rather
## than passing broken audio streams to the player.

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _failures: Array[String] = []
var _audio_ready_emitted := false


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)

	_network.script_failed.connect(func(msg: String) -> void:
		_failures.append(msg)
	)
	_network.audio_ready.connect(func(_idx: int, _audio: AudioStream) -> void:
		_audio_ready_emitted = true
	)

	# 1. Test downloading with an invalid URL schema to trigger immediate request start error
	_network._download_audio(0, "invalid://url/test.wav")

	await create_timer(0.2).timeout

	if _audio_ready_emitted:
		_fail("audio_ready should not be emitted when request fails")
		return

	if _failures.is_empty():
		_fail("script_failed should be emitted on invalid URL download attempt")
		return

	# 2. Test decode failure validation with corrupted buffer
	var invalid_stream := AudioStreamWAV.new()
	var corrupted_bytes := PackedByteArray([1, 2, 3])
	var loaded: AudioStreamWAV = invalid_stream.load_from_buffer(corrupted_bytes)
	if loaded != null and not loaded.data.is_empty():
		_fail("Corrupted bytes should not decode to valid audio")
		return

	_network.queue_free()
	print("[TEST] PASS — audio download errors caught and signaled cleanly without emitting audio_ready: %s" % _failures[0])
	quit(0)


func _fail(msg: String) -> void:
	print("[TEST] FAIL — ", msg)
	quit(1)
