extends SceneTree
## Headless integration test: WebSocket live updates + community voting.
## Drives the REAL autoload singleton (resolved at runtime) against a live server.
## Verifies:
##  1. connect_ws() -> ws_connected -> ws_state_snapshot (cast on connect)
##  2. news/refresh with fresh mock stories -> ws_script_delta broadcast
##  3. cast_vote() -> vote_result with counted=true + winner tally

var _steps := 0
var _passed := false


func _init() -> void:
	print("[TEST] connecting ws...")
	await process_frame
	# Autoloads are attached to root during startup; resolve after the first frame.
	var network: Node = root.get_node("Network")
	network.base_url = "http://127.0.0.1:8000"
	network.api_key = "dev-api-key"
	network.client_id = "godot-integration"
	network.script_failed.connect(_on_failed)
	network.ws_connected.connect(_on_ws_connected)
	network.ws_state_snapshot.connect(_on_state_snapshot)
	network.ws_script_delta.connect(_on_script_delta)
	network.vote_result.connect(_on_vote_result)
	# Reset the socket the autoload opened at startup with the default key.
	network.disconnect_ws()
	network.connect_ws()
	create_timer(40.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — steps=%d" % _steps)
			quit(1)
	)


func _on_ws_connected() -> void:
	_steps += 1
	print("[TEST] ws_connected (step %d)" % _steps)
	# Trigger a broadcast: fresh mock stories -> script_delta pushed.
	var network: Node = root.get_node("Network")
	network.refresh_news()


func _on_state_snapshot(characters: Dictionary) -> void:
	_steps += 1
	print("[TEST] state_snapshot chars=%d (step %d)" % [characters.size(), _steps])
	if characters.is_empty():
		print("[TEST] WARN — snapshot empty (fresh cast is fine)")


func _on_script_delta(delta: Dictionary) -> void:
	_steps += 1
	print("[TEST] script_delta headline='%s' (step %d)" % [delta.get("headline", ""), _steps])
	var script_id: String = delta.get("script_id", "")
	if script_id == "":
		print("[TEST] FAIL — delta missing script_id")
		quit(1)
	var network: Node = root.get_node("Network")
	network.cast_vote(script_id, "furaha")


func _on_vote_result(payload: Dictionary) -> void:
	_steps += 1
	print("[TEST] vote_result counted=%s winner=%s total=%d (step %d)" % [
		payload.get("counted", false),
		payload.get("winner", ""),
		payload.get("total", 0),
		_steps,
	])
	if payload.get("counted", false) == true and payload.get("winner", "") != "":
		print("[TEST] PASS — WS live + voting verified in %d steps" % _steps)
		_passed = true
		quit(0)
	else:
		print("[TEST] FAIL — unexpected vote response: %s" % str(payload))
		quit(1)


func _on_failed(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)