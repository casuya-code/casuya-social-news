extends SceneTree
## Headless integration test for the headline ticker (ui/NewsTicker.gd).
## Verifies:
## - push() keeps a bounded queue, newest first, dedupes empties/duplicates
## - rotation advances the visible headline over time
## - clear() empties the feed and stops rotation

const TICKER_SCRIPT := preload("res://ui/NewsTicker.gd")

var _ticker: Label
var _passed := false


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	_ticker = TICKER_SCRIPT.new()
	root.add_child(_ticker)

	# --- bounded, newest-first, dedupe ---
	for i in range(10):
		_ticker.push("Kichwa cha habari %d" % i)
	if _ticker.count() != 6:
		_fail("ticker should cap at 6 headlines, has %d" % _ticker.count())
		return
	var first: String = _ticker.text
	if not first.contains("Kichwa cha habari 9"):
		_fail("newest headline should show first, text='%s'" % first)
		return
	if not first.begins_with("KUHUSU LEO: "):
		_fail("ticker missing prefix: %s" % first)
		return

	# Duplicate + empty pushes must be ignored.
	_ticker.push("Kichwa cha habari 9")
	_ticker.push("   ")
	if _ticker.count() != 6:
		_fail("duplicate/empty pushes should be ignored, count=%d" % _ticker.count())
		return

	# --- rotation advances the shown headline ---
	await create_timer(_ticker.ROTATE_INTERVAL_S + 0.3).timeout
	if _ticker.text == first:
		_fail("ticker did not rotate to the next headline")
		return

	# --- clear ---
	_ticker.clear()
	if _ticker.count() != 0 or _ticker.text != "":
		_fail("clear() should empty the feed")
		return

	print("[TEST] PASS — bounded queue, dedupe, rotation, clear")
	_passed = true
	quit(0)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)