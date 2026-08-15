extends SceneTree
## Headless integration test: verifies transport-failure retry in NetworkManager.
## - A request to a dead endpoint retries with backoff and finally fails after
##   exhausting attempts (script_failed with the retry count).
## - A request to the live server succeeds (script_loaded, no retries).

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _retry_events := 0
var _live_script := false
var _dead_failed := false


func _init() -> void:
	_run()


func _run() -> void:
	# Let the scene tree settle so HTTPRequest is usable in this harness.
	await process_frame
	await process_frame

	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "test-key"
	_network.script_loaded.connect(_on_script_loaded)
	_network.script_failed.connect(_on_script_failed)
	_network.retry_scheduled.connect(_on_retry_scheduled)

	# Live server: should succeed with zero retries.
	_network.base_url = "http://127.0.0.1:8000"
	var unique := str(Time.get_unix_time_from_system())
	_network.generate_script(
		"Habari za retry test", "Godot Test",
		"https://example.com/retry-%s" % unique
	)
	await create_timer(8.0).timeout
	if not _live_script:
		_fail("live generate_script did not succeed")
		return
	if _retry_events != 0:
		_fail("live request triggered %d retries (expected 0)" % _retry_events)
		return

	# Dead endpoint: must retry with backoff, then fail after attempts.
	_network._retry.max_retries = 3
	_network._retry.base_delay_s = 0.2
	_network.base_url = "http://127.0.0.1:9"
	_network.generate_script("Dead", "Godot Test", "https://example.com/dead")
	await create_timer(40.0).timeout
	if not _dead_failed:
		_fail("dead request did not fail after retries (retry_events=%d)" % _retry_events)
		return
	if _retry_events < 3:
		_fail("expected >=3 retries on dead endpoint, got %d" % _retry_events)
		return

	print("[TEST] PASS — live succeeds without retry; dead retries %d times then fails" % _retry_events)
	quit(0)


func _on_script_loaded(script: Dictionary) -> void:
	print("[TEST] live script_loaded id=", script.get("script_id", ""))
	_live_script = true


func _on_script_failed(message: String) -> void:
	print("[TEST] script_failed: ", message)
	if _live_script:
		_dead_failed = true


func _on_retry_scheduled(tag: String, attempt: int, delay_s: float) -> void:
	_retry_events += 1
	print("[TEST] retry tag=", tag, " attempt=", attempt, " delay=%.2f" % delay_s)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)