class_name OfflineDetector
extends Node
## Connectivity watchdog. Probes `GET /api/v1/health` on a timer; emits
## `status_changed(is_offline)` only when the state actually flips, so the UI
## can show a "Nje ya mtandao" banner without spam.

signal status_changed(is_offline: bool)

const PROBE_PATH := "/api/v1/health"
const PROBE_TIMEOUT_S := 5.0

var base_url: String = "http://127.0.0.1:8000"
var api_key: String = "dev-api-key"
var probe_interval_s := 5.0

var is_offline := false
var _has_probed := false

var _timer: Timer
var _in_flight := false


func _ready() -> void:
	_ensure_timer()


func _ensure_timer() -> void:
	if _timer != null:
		return
	_timer = Timer.new()
	_timer.wait_time = probe_interval_s
	_timer.timeout.connect(_probe)
	add_child(_timer)


func start() -> void:
	_ensure_timer()
	_timer.start()


func stop() -> void:
	if _timer != null:
		_timer.stop()
	if _in_flight:
		_set_offline(false)


func _probe() -> void:
	if _in_flight:
		return
	_in_flight = true
	var http := HTTPRequest.new()
	http.timeout = PROBE_TIMEOUT_S
	add_child(http)
	http.request_completed.connect(
		func(result: int, _code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
			_in_flight = false
			_set_offline(result != HTTPRequest.RESULT_SUCCESS)
			http.queue_free()
	)
	var err := http.request(
		base_url + PROBE_PATH,
		PackedStringArray(["X-API-Key: %s" % api_key])
	)
	if err != OK:
		_in_flight = false
		_set_offline(true)
		http.queue_free()


func _set_offline(value: bool) -> void:
	# Emit on every state change AND on the first probe, so consumers learn the
	# initial connectivity even when it matches the starting value.
	if not _has_probed or is_offline != value:
		_has_probed = true
		is_offline = value
		status_changed.emit(is_offline)