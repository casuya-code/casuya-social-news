extends SceneTree
## Headless integration test for influence tracking (Feature #35, client side).
## Drives NetworkManager against a live server. Verifies:
## - refresh_news -> news_loaded (a script_id to vote on)
## - cast_vote -> vote_result (counted)
## - fetch_influence -> influence_loaded with scripts_influenced >= 1

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _script_id := ""
var _voted := false
var _influence_loaded := false
var _passed := false
var _unique := str(Time.get_unix_time_from_system())


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "test-key"
	_network.base_url = "http://127.0.0.1:8000"
	_network.client_id = "godot-influence-%s" % _unique
	_network.script_failed.connect(_on_failed)
	_network.api_error.connect(_on_api_error)
	_network.script_loaded.connect(_on_script_loaded)
	_network.vote_result.connect(_on_vote_result)
	_network.influence_loaded.connect(_on_influence_loaded)
	await process_frame
	_network.generate_script(
		"Habari za ushawishi %s" % _unique,
		"Influence Test",
		"https://example.com/influence-%s" % _unique,
	)
	create_timer(30.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — script_id=%s voted=%s influence=%s" % [_script_id, _voted, _influence_loaded])
			quit(1)
	)


func _on_script_loaded(script: Dictionary) -> void:
	_script_id = script.get("script_id", "")
	if _script_id == "":
		_fail("generated script has no script_id")
		return
	_network.cast_vote(_script_id, "utulivu")


func _on_vote_result(payload: Dictionary) -> void:
	_voted = true
	print("[TEST] vote_result counted=%s winner=%s total=%d" % [
		payload.get("counted", false),
		payload.get("winner", ""),
		payload.get("total", 0),
	])
	if payload.get("counted", false) != true:
		_fail("vote not counted: %s" % str(payload))
		return
	_network.fetch_influence()


func _on_influence_loaded(payload: Dictionary) -> void:
	_influence_loaded = true
	var influenced: int = payload.get("scripts_influenced", 0)
	print("[TEST] influence client=%s scripts=%d" % [
		payload.get("client_id", ""),
		influenced,
	])
	if influenced < 1:
		_fail("expected scripts_influenced >= 1, got %d" % influenced)
		return
	if payload.get("client_id", "") != _network.client_id:
		_fail("influence returned wrong client_id")
		return
	print("[TEST] PASS — vote counted + influence reflects the client's steering")
	_passed = true
	quit(0)


func _on_api_error(error_code: String, message: String) -> void:
	_fail("api_error %s: %s" % [error_code, message])


func _on_failed(message: String) -> void:
	_fail(message)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)