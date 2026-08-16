extends SceneTree
## Headless integration test for error-code UX (Feature: error codes).
## - ErrorCatalog maps every documented code to friendly Swahili text and
##   flags transient codes (no server needed).
## - NetworkManager emits `api_error(error_code, message)` for envelope
##   failures (live server: fetching a missing script yields E3001) while
##   transport failures still use `script_failed`.

const NETWORK_SCRIPT := preload("res://autoload/NetworkManager.gd")
const CATALOG_SCRIPT := preload("res://network/ErrorCatalog.gd")

var _network: Node
var _got_api_error := false
var _passed := false


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame

	# --- ErrorCatalog: all documented codes map to friendly text ---
	var codes := ["E0000", "E1001", "E1002", "E1003", "E2001", "E2002",
		"E2003", "E3001", "E3002", "E3003", "E4001", "E4002",
		"E4003", "E5001", "E5002"]
	for code in codes:
		var friendly: String = CATALOG_SCRIPT.describe(code)
		if friendly.is_empty() or friendly.contains("code:"):
			_fail("catalog produced no friendly text for %s" % code)
			return

	if not CATALOG_SCRIPT.is_transient("E1003"):
		_fail("E1003 should be transient")
		return
	if CATALOG_SCRIPT.is_transient("E3001"):
		_fail("E3001 should NOT be transient")
		return
	if not CATALOG_SCRIPT.describe("E5001", "raw").contains("akiba"):
		_fail("E5001 should mention offline fallback (akiba)")
		return

	# --- live: fetch a missing script -> E3001 via api_error ---
	_network = NETWORK_SCRIPT.new()
	_network.ws_enabled = false
	root.add_child(_network)
	_network.api_key = "dev-api-key"
	_network.base_url = "http://127.0.0.1:8000"
	_network.api_error.connect(_on_api_error)
	_network.script_failed.connect(_on_script_failed)
	await process_frame
	_network.fetch_script("does-not-exist-%s" % str(Time.get_unix_time_from_system()))
	create_timer(20.0).timeout.connect(func():
		if not _passed:
			print("[TEST] TIMEOUT — no api_error received")
			quit(1)
	)


func _on_api_error(error_code: String, message: String) -> void:
	_got_api_error = true
	if error_code != "E3001":
		_fail("expected E3001, got %s (%s)" % [error_code, message])
		return
	if message.is_empty():
		_fail("api_error carried no message")
		return
	# Friendly mapping of E3001 must reach the UI-facing describe().
	var friendly: String = CATALOG_SCRIPT.describe(error_code, message)
	if friendly.contains("code:"):
		_fail("friendly text still raw: %s" % friendly)
		return
	print("[TEST] PASS — api_error=%s friendly=%s" % [error_code, friendly])
	_passed = true
	quit(0)


func _on_script_failed(message: String) -> void:
	# Envelope failures must NOT also fire script_failed (transport-only now).
	if _got_api_error:
		_fail("script_failed fired alongside api_error: %s" % message)
		quit(1)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)