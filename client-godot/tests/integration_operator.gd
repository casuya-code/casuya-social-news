extends SceneTree
## Headless integration test: drives the operator console network calls
## against the live server. Verifies fetch_health -> health_loaded,
## fetch_script_list -> script_list_loaded, run_retention -> retention_result.

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _health_ok := false
var _list_ok := false
var _retention_ok := false
var _passed := false


func _init() -> void:
	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "test-key"
	_network.base_url = "http://127.0.0.1:8000"
	_network.script_failed.connect(_on_failed)
	_network.health_loaded.connect(_on_health)
	_network.script_list_loaded.connect(_on_script_list)
	_network.retention_result.connect(_on_retention)
	print("[TEST] fetching operator health...")
	await process_frame
	_network.fetch_health()
	create_timer(40.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — no operator data received")
			quit(1)
	)


func _on_health(payload: Dictionary) -> void:
	_health_ok = true
	print("[TEST] health status:", payload.get("status", "?"))
	var deps: Dictionary = payload.get("dependencies", {})
	print("[TEST] db=", deps.get("database", "?"), " cache=", deps.get("cache", "?"), " tts=", deps.get("tts", "?"))
	var sched: Dictionary = payload.get("scheduler", {})
	print("[TEST] scheduler cycles=", sched.get("cycles_completed", 0))
	_network.fetch_script_list(5)
	_network.run_retention(true)


func _on_script_list(scripts: Array) -> void:
	_list_ok = true
	print("[TEST] script_list count=", scripts.size())
	_check_done()


func _on_retention(payload: Dictionary) -> void:
	_retention_ok = true
	var audio: Dictionary = payload.get("audio", {})
	print("[TEST] retention dry_run=", payload.get("dry_run", "?"), " audio_purged=", audio.get("purged", 0))
	_check_done()


func _check_done() -> void:
	if not (_health_ok and _list_ok and _retention_ok):
		return
	print("[TEST] PASS — health, script list, and retention dry-run all received")
	_passed = true
	quit(0)


func _on_failed(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)