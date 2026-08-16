extends SceneTree
## Headless integration test: drives OfflineDetector against a reachable and a
## dead endpoint. Verifies the probe reports online for a live server and
## offline for a dead port.

const OfflineDetectorScene := preload("res://ui/OfflineDetector.gd")

var _live_online := false
var _dead_offline := false


func _init() -> void:
	_run()


func _run() -> void:
	# Let the scene tree settle so HTTPRequest is usable in this harness.
	await process_frame
	await process_frame

	# Reachable live server.
	var live: Node = OfflineDetectorScene.new()
	live.base_url = "http://127.0.0.1:8000"
	live.api_key = "dev-api-key"
	live.probe_interval_s = 0.5
	root.add_child(live)
	live.status_changed.connect(_on_live_changed)
	live.start()

	# Dead port — should flip to offline.
	var dead: Node = OfflineDetectorScene.new()
	dead.base_url = "http://127.0.0.1:9"
	dead.api_key = "dev-api-key"
	dead.probe_interval_s = 0.5
	root.add_child(dead)
	dead.status_changed.connect(_on_dead_changed)
	dead.start()

	await create_timer(8.0).timeout
	if _live_online and _dead_offline:
		print("[TEST] PASS — offline detector reports live=online, dead=offline")
		quit(0)
	else:
		_fail("live_online=%s dead_offline=%s" % [_live_online, _dead_offline])


func _on_live_changed(is_offline: bool) -> void:
	print("[TEST] live probe is_offline=", is_offline)
	if not is_offline:
		_live_online = true


func _on_dead_changed(is_offline: bool) -> void:
	print("[TEST] dead probe is_offline=", is_offline)
	if is_offline:
		_dead_offline = true


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)