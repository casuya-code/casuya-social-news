extends Label
## News ticker — rotates recent story headlines on screen so the room always
## sees what the engine is writing. Keeps a small queue (newest first),
## shows one headline at a time and advances every few seconds.
##
## Single responsibility: a bounded rotating headline feed for the UI.

const MAX_HEADLINES := 6
const ROTATE_INTERVAL_S := 4.0
const PREFIX := "KUHUSU LEO: "

var _headlines: Array[String] = []
var _index := 0
var _timer: SceneTreeTimer


## Push a headline (ignored if empty or already queued).
func push(headline: String) -> void:
	var clean := headline.strip_edges()
	if clean == "":
		return
	if clean in _headlines:
		return
	_headlines.insert(0, clean)
	if _headlines.size() > MAX_HEADLINES:
		_headlines.resize(MAX_HEADLINES)
	_show_current()
	_restart_timer()


## Clear all headlines and stop rotating.
func clear() -> void:
	_headlines.clear()
	_index = 0
	text = ""
	if _timer != null:
		_timer.timeout.disconnect(_advance)


## How many headlines are queued (useful for tests).
func count() -> int:
	return _headlines.size()


func _show_current() -> void:
	if _headlines.is_empty():
		text = ""
		return
	if _index >= _headlines.size():
		_index = 0
	text = PREFIX + _headlines[_index]


func _advance() -> void:
	if _headlines.is_empty():
		return
	_index = (_index + 1) % _headlines.size()
	_show_current()
	_restart_timer()


func _restart_timer() -> void:
	if _timer != null:
		_timer.timeout.disconnect(_advance)
	_timer = get_tree().create_timer(ROTATE_INTERVAL_S)
	_timer.timeout.connect(_advance)