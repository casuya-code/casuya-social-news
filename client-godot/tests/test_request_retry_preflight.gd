extends SceneTree
## Headless test for Pre-flight Request Retry Coverage:
## Verifies that NetworkManager's _request routes request start failures (e.g. malformed URLs)
## through the RetryHandler backoff and emits retry_scheduled rather than immediately failing.

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _scheduled_retries: Array[Dictionary] = []
var _final_failure := ""


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	_network._max_retries = 2
	_network._retry_delay_s = 0.05
	root.add_child(_network)

	_network.retry_scheduled.connect(func(tag: String, attempt: int, delay: float) -> void:
		_scheduled_retries.append({"tag": tag, "attempt": attempt, "delay": delay})
		print("[TEST] retry scheduled tag=%s attempt=%d delay=%.2f" % [tag, attempt, delay])
	)

	_network.script_failed.connect(func(msg: String) -> void:
		_final_failure = msg
		print("[TEST] script_failed received: %s" % msg)
	)

	# Trigger a request with an invalid URL scheme that fails at http.request()
	_network._request("preflight_test", "invalid://bad-url", HTTPClient.METHOD_GET)

	# Wait for retries to cycle (attempt 1, attempt 2, final failure)
	await create_timer(0.4).timeout

	if _scheduled_retries.size() != 2:
		_fail("Expected 2 retry_scheduled events for _max_retries=2, got %d" % _scheduled_retries.size())
		return

	if _final_failure == "":
		_fail("Expected terminal script_failed emission after retry exhaustion")
		return

	_network.queue_free()
	print("[TEST] PASS — preflight request failures correctly routed through RetryHandler backoff")
	quit(0)


func _fail(msg: String) -> void:
	print("[TEST] FAIL — ", msg)
	quit(1)
