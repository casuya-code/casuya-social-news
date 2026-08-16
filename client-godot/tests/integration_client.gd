extends SceneTree
## Headless integration test: drives NetworkManager against the live server.
## Verifies: generate_script -> script_loaded -> generate_audio -> audio_ready.

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _current: Dictionary = {}
var _audio_count := 0
var _passed := false
var _unique_id := str(Time.get_unix_time_from_system())


func _init() -> void:
	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "dev-api-key"
	_network.base_url = "http://127.0.0.1:8000"
	_network.script_failed.connect(_on_failed)
	_network.script_loaded.connect(_on_script_loaded)
	_network.audio_ready.connect(_on_audio_ready)
	print("[TEST] generating script...")
	await process_frame
	_network.generate_script(
		"Habari za mtihani wa Godot",
		"Godot Test",
		"https://example.com/godot-client-%s" % _unique_id
	)
	create_timer(40.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — no audio received")
			quit(1)
	)


func _on_script_loaded(script: Dictionary) -> void:
	_current = script
	print("[TEST] script_loaded id:", script.get("script_id", ""))
	print("[TEST] lines:", (_current.get("lines", []) as Array).size())
	_network.generate_audio(_current)


func _on_audio_ready(line_index: int, audio: AudioStream) -> void:
	_audio_count += 1
	var seconds: float = audio.get_length() if audio else 0.0
	print("[TEST] audio_ready line=%d length=%.2fs" % [line_index, seconds])
	var expected := (_current.get("lines", []) as Array).size()
	if _audio_count == expected:
		print("[TEST] PASS — received all %d audio streams" % _audio_count)
		_passed = true
		quit(0)


func _on_failed(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)