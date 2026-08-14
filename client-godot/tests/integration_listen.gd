extends SceneTree
## Headless integration test: live listen mode.
## Verifies the client can fetch a full script by id after a `script_delta`
## broadcast and drive it through generate_audio -> audio_ready (the exact
## path listen mode uses), without pressing Start.

var _steps := 0
var _passed := false
var _script_id := ""


func _init() -> void:
	print("[TEST] resolving autoload...")
	await process_frame
	var network: Node = root.get_node("Network")
	network.base_url = "http://127.0.0.1:8000"
	network.api_key = "test-key"
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
	print("[TEST] script_delta id=%s (step %d)" % [_script_id, _steps])
	if _script_id == "":
		print("[TEST] FAIL — delta missing script_id")
		quit(1)
	# This is what listen mode does: fetch the full script by id.
	root.get_node("Network").fetch_script(_script_id)


func _on_script_loaded(script: Dictionary) -> void:
	_steps += 1
	print("[TEST] script_loaded id=%s lines=%d (step %d)" % [
		script.get("script_id", ""),
		(script.get("lines", []) as Array).size(),
		_steps,
	])
	if script.get("script_id", "") != _script_id:
		print("[TEST] FAIL — fetched wrong script")
		quit(1)
	# Drive it through audio generation, exactly like _start_script does.
	root.get_node("Network").generate_audio(script)


func _on_audio_ready(line_index: int, _audio: AudioStream) -> void:
	_steps += 1
	print("[TEST] audio_ready line=%d (step %d)" % [line_index, _steps])
	if line_index >= 3:
		print("[TEST] PASS — listen flow verified in %d steps" % _steps)
		_passed = true
		quit(0)


func _on_failed(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)