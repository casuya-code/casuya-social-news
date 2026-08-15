extends SceneTree
## Headless integration test for live vote stats (Feature #35, client side).
## Drives NetworkManager against a live server. Verifies:
## - fetch_vote_stats on a fresh script shows total == 0 (no votes yet)
## - cast_vote -> vote_result (counted)
## - fetch_vote_stats again reflects the vote in the tally

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")

var _network: Node
var _script_id := ""
var _unique := str(Time.get_unix_time_from_system())
var _stats_before := -1
var _stats_after := -1
var _voted := false
var _passed := false


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "test-key"
	_network.base_url = "http://127.0.0.1:8000"
	_network.client_id = "godot-stats-%s" % _unique
	_network.script_failed.connect(_on_failed)
	_network.api_error.connect(_on_api_error)
	_network.script_loaded.connect(_on_script_loaded)
	_network.vote_stats_loaded.connect(_on_vote_stats_loaded)
	_network.vote_result.connect(_on_vote_result)
	await process_frame
	_network.generate_script(
		"Habari za kura %s" % _unique,
		"Stats Test",
		"https://example.com/stats-%s" % _unique,
	)
	create_timer(30.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — stats_before=%d stats_after=%d voted=%s" % [_stats_before, _stats_after, _voted])
			quit(1)
	)


func _on_script_loaded(script: Dictionary) -> void:
	_script_id = script.get("script_id", "")
	if _script_id == "":
		_fail("generated script has no script_id")
		return
	# 1) Stats on a fresh script: no votes yet.
	_network.fetch_vote_stats(_script_id)


func _on_vote_stats_loaded(payload: Dictionary) -> void:
	var total: int = payload.get("total", 0)
	if _stats_before == -1:
		_stats_before = total
		print("[TEST] stats before vote: total=%d winner=%s" % [total, payload.get("winner", "")])
		if total != 0:
			_fail("fresh script should have 0 votes, got %d" % total)
			return
		_network.cast_vote(_script_id, "msisimko")
	else:
		_stats_after = total
		print("[TEST] stats after vote: total=%d winner=%s" % [total, payload.get("winner", "")])
		if total < 1:
			_fail("vote did not appear in stats")
			return
		if payload.get("winner", "") != "msisimko":
			_fail("expected winner msisimko, got %s" % payload.get("winner", ""))
			return
		print("[TEST] PASS — stats reflect community pulse before + after voting")
		_passed = true
		quit(0)


func _on_vote_result(payload: Dictionary) -> void:
	_voted = true
	if payload.get("counted", false) != true:
		_fail("vote not counted: %s" % str(payload))
		return
	# 2) Stats after voting: the tally must include our vote.
	_network.fetch_vote_stats(_script_id)


func _on_api_error(error_code: String, message: String) -> void:
	_fail("api_error %s: %s" % [error_code, message])


func _on_failed(message: String) -> void:
	_fail(message)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)