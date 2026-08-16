extends SceneTree
## Headless integration test: live listen mode.
## Verifies the client can fetch a full script by id after a `script_delta`
## broadcast and drive it through generate_audio -> audio_ready (the exact
## path listen mode uses), without pressing Start.

var _steps := 0
var _passed := false
var _script_id := ""
var _script_lines := 0
var _lines_seen := {}


func _init() -> void:
	print("[TEST] resolving autoload...")
	await process_frame
	var network: Node = root.get_node("Network")
	network.base_url = "http://127.0.0.1:8000"
	network.api_key = "dev-api-key"
	network.client_id = "godot-listen"
	network.script_failed.connect(_on_failed)
	network.ws_connected.connect(_on_ws_connected)
	network.ws_script_delta.connect(_on_script_delta)
	network.script_loaded.connect(_on_script_loaded)
	network.audio_ready.connect(_on_audio_ready)
	network.disconnect_ws()
	network.connect_ws()
	create_timer(45.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — steps=%d" % _steps)
			quit(1)
	)


func _on_ws_connected() -> void:
	_steps += 1
	print("[TEST] ws_connected (step %d)" % _steps)
	# Trigger a broadcast: fresh mock stories -> script_delta pushed.
	root.get_node("Network").refresh_news()


func _on_script_delta(delta: Dictionary) -> void:
	_steps += 1
	_script_id = delta.get("script_id", "")
	_script_lines = 0
	_lines_seen.clear()
	print("[TEST] script_delta id=%s (step %d)" % [_script_id, _steps])
	if _script_id == "":
		print("[TEST] FAIL — delta missing script_id")
		quit(1)
	# This is what listen mode does: fetch the full script by id.
	root.get_node("Network").fetch_script(_script_id)


func _on_script_loaded(script: Dictionary) -> void:
	_steps += 1
	_script_lines = (script.get("lines", []) as Array).size()
	print("[TEST] script_loaded id=%s lines=%d (step %d)" % [
		script.get("script_id", ""),
		_script_lines,
		_steps,
	])
	if script.get("script_id", "") != _script_id:
		print("[TEST] FAIL — fetched wrong script")
		quit(1)
	# Drive it through audio generation, exactly like _start_script does.
	root.get_node("Network").generate_audio(script)


func _on_audio_ready(line_index: int, _audio: AudioStream) -> void:
	_steps += 1
	_lines_seen[line_index] = true
	print("[TEST] audio_ready line=%d (step %d)" % [line_index, _steps])
	if _lines_seen.size() == _script_lines and _script_lines > 0:
		print("[TEST] PASS — listen flow verified in %d steps" % _steps)
		_passed = true
		quit(0)


func _on_failed(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)