extends Node
## NetworkManager — single autoload for all server communication.
## Attach as an autoload named "Network" in Project Settings.
##
## Responsibilities:
##  - Fetch a script (news -> dialogue) from the server
##  - Fetch/synthesize audio for each line
##  - Live WebSocket updates (Feature #27): state_snapshot + script_delta
##  - Community voting (Feature #35): cast vote on story direction
##  - Offline detection and queued retries (Feature: OfflineDetector)

signal script_loaded(script: Dictionary)
signal news_loaded(scripts: Array)
signal script_failed(message: String)
signal api_error(error_code: String, message: String)
signal audio_ready(line_index: int, audio: AudioStream)
signal offline_status_changed(is_offline: bool)
signal ws_connected
signal ws_disconnected
signal ws_state_snapshot(characters: Dictionary)
signal ws_script_delta(delta: Dictionary)
signal vote_result(payload: Dictionary)
signal health_loaded(payload: Dictionary)
signal script_list_loaded(scripts: Array)
signal retention_result(payload: Dictionary)
signal retry_scheduled(tag: String, attempt: int, delay_s: float)
signal weather_loaded(payload: Dictionary)
signal influence_loaded(payload: Dictionary)
signal vote_stats_loaded(payload: Dictionary)
signal latest_news_loaded(payload: Dictionary)

const DEFAULT_BASE_URL := "http://127.0.0.1:8000"
const API_PREFIX := "/api/v1"
const DEFAULT_API_KEY := "dev-api-key"
const WS_PREFIX := "/api/v1/ws"
const VOTE_PATH := "/api/v1/economy/vote"
const REQUEST_TIMEOUT_S := 8.0

var base_url: String = DEFAULT_BASE_URL
var api_key: String = DEFAULT_API_KEY
var client_id: String = "godot-client"
var is_offline := false
var ws_enabled := true
var cache: Node  # OfflineCache instance (optional; wired by main.gd)
var audio_quality := "high"  # TTS quality param: "high" | "low"

var _ws: WebSocketPeer
var _ws_open := false
var _pending: Array[Dictionary] = []
var _max_retries := 3
var _retry_delay_s := 1.0
var _retry: RetryHandler
var _current_script_id := ""


func _ready() -> void:
	_retry = RetryHandler.new()
	_retry.max_retries = _max_retries
	_retry.base_delay_s = _retry_delay_s
	if ws_enabled:
		connect_ws()


func _process(_delta: float) -> void:
	if _ws == null:
		return
	_ws.poll()
	match _ws.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			if not _ws_open:
				_ws_open = true
				ws_connected.emit()
			while _ws.get_available_packet_count() > 0:
				var packet := _ws.get_packet()
				var message: Variant = JSON.parse_string(packet.get_string_from_utf8())
				if message is Dictionary:
					_handle_ws_message(message)
		WebSocketPeer.STATE_CLOSING, WebSocketPeer.STATE_CLOSED:
			if _ws_open:
				_ws_open = false
				ws_disconnected.emit()
			_ws = null


func _handle_ws_message(message: Dictionary) -> void:
	match message.get("type", ""):
		"state_snapshot":
			ws_state_snapshot.emit(message.get("characters", []))
		"script_delta":
			ws_script_delta.emit(message)


func connect_ws() -> void:
	if _ws != null:
		return
	var ws_url := _ws_url()
	_ws = WebSocketPeer.new()
	_ws_open = false
	var err := _ws.connect_to_url(ws_url)
	if err != OK:
		_ws = null
		script_failed.emit("WebSocket connect failed (code %d)" % err)
		return


func disconnect_ws() -> void:
	if _ws != null:
		_ws.close()
		_ws = null
	if _ws_open:
		_ws_open = false
		ws_disconnected.emit()


func is_ws_connected() -> bool:
	return _ws != null and _ws.get_ready_state() == WebSocketPeer.STATE_OPEN


func _ws_url() -> String:
	var ws_base := base_url.replace("http://", "ws://").replace("https://", "wss://")
	return "%s%s?api_key=%s" % [ws_base, WS_PREFIX, api_key]


## Cast (or change) this client's vote on a story's direction.
func cast_vote(script_id: String, direction: String) -> void:
	var body := JSON.stringify({
		"script_id": script_id,
		"client_id": client_id,
		"direction": direction,
	})
	_request("vote", base_url + VOTE_PATH, HTTPClient.METHOD_POST, body)


## Fetch how many distinct stories this client has steered via votes.
func fetch_influence() -> void:
	_request(
		"influence",
		base_url + API_PREFIX + "/economy/influence/" + client_id,
		HTTPClient.METHOD_GET
	)


## Fetch the live tally + winning direction for a story's votes.
func fetch_vote_stats(script_id: String) -> void:
	_request(
		"stats",
		base_url + API_PREFIX + "/economy/stats/" + script_id,
		HTTPClient.METHOD_GET
	)


## Generate a script from a news headline.
func generate_script(headline: String, source: String, url: String) -> void:
	var body := JSON.stringify({
		"headline": headline,
		"source": source,
		"url": url,
	})
	_request("generate", base_url + API_PREFIX + "/scripts/generate", HTTPClient.METHOD_POST, body)


## Synthesize audio for every line of a script.
func generate_audio(script: Dictionary) -> void:
	_current_script_id = script.get("script_id", "")
	var body := JSON.stringify({"script": script, "quality": audio_quality})
	_request("audio", base_url + API_PREFIX + "/scripts/generate-audio", HTTPClient.METHOD_POST, body)


## Pull fresh news and generate a script for each new story ("endless loop").
func refresh_news() -> void:
	_request("news", base_url + API_PREFIX + "/news/refresh", HTTPClient.METHOD_POST)


## Fetch the most recent ingested news articles (no script generation).
func fetch_latest_news(limit: int = 20) -> void:
	_request(
		"latest_news",
		base_url + API_PREFIX + "/news/latest?limit=%d" % limit,
		HTTPClient.METHOD_GET
	)


## Fetch a previously generated script by id (for live listen mode).
func fetch_script(script_id: String) -> void:
	_request("fetch", base_url + API_PREFIX + "/scripts/" + script_id, HTTPClient.METHOD_GET)


## Fetch the operator health snapshot (status, dependencies, scheduler).
func fetch_health() -> void:
	_request("health", base_url + API_PREFIX + "/health", HTTPClient.METHOD_GET)


## Fetch the current weather + time-of-day mood bias for the drama.
func fetch_weather() -> void:
	_request("weather", base_url + API_PREFIX + "/weather", HTTPClient.METHOD_GET)


## Fetch a paginated list of recent scripts for operator/QA browsing.
func fetch_script_list(limit: int = 10) -> void:
	_request(
		"script_list",
		base_url + API_PREFIX + "/scripts?limit=%d" % limit,
		HTTPClient.METHOD_GET
	)


## Trigger the retention sweep (or a dry-run preview of it).
func run_retention(dry_run: bool = false) -> void:
	var suffix := "?dry_run=true" if dry_run else ""
	_request(
		"retention",
		base_url + API_PREFIX + "/maintenance/retention" + suffix,
		HTTPClient.METHOD_POST
	)


## Fire one request on its own HTTPRequest node (so parallel calls never clash).
func _request(tag: String, url: String, method: HTTPClient.Method, body: String = "") -> void:
	var http := HTTPRequest.new()
	http.timeout = REQUEST_TIMEOUT_S
	add_child(http)
	http.request_completed.connect(
		func(result: int, code: int, headers: PackedStringArray, res_body: PackedByteArray) -> void:
			if result != HTTPRequest.RESULT_SUCCESS:
				if _retry.register_failure(tag):
					var delay := _retry.delay_for(tag)
					retry_scheduled.emit(tag, _retry.attempts_for(tag), delay)
					http.queue_free()
					_retry_after(tag, url, method, body, delay)
					return
				_retry.reset(tag)
				http.queue_free()
				script_failed.emit("Network error: %d (after %d retries)" % [
					result, _max_retries
				])
				return
			_retry.reset(tag)
			_on_request_completed(tag, result, code, headers, res_body)
			http.queue_free()
	)
	var err := http.request(url, _auth_headers(body != ""), method, body)
	if err != OK:
		http.queue_free()
		script_failed.emit("Request failed to start (code %d)" % err)


## Re-issue a transport-failed request after the backoff delay.
func _retry_after(tag: String, url: String, method: HTTPClient.Method, body: String, delay: float) -> void:
	var timer := get_tree().create_timer(delay)
	timer.timeout.connect(func() -> void: _request(tag, url, method, body))


func _auth_headers(is_json: bool) -> PackedStringArray:
	var headers := PackedStringArray()
	headers.append("X-API-Key: %s" % api_key)
	if is_json:
		headers.append("Content-Type: application/json")
	return headers


func _on_request_completed(tag: String, result: int, _code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		script_failed.emit("Network error: %d" % result)
		return

	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		script_failed.emit("Malformed JSON from server")
		return

	var data: Variant = json.data

	# The server wraps failures in an envelope; successes come back flat.
	if data is Dictionary and data.get("success", true) == false:
		var error_code := String(data.get("error_code", "E0000"))
		api_error.emit(error_code, String(data.get("message", "Unknown server error")))
		return

	if tag == "vote":
		vote_result.emit(data)
		return

	if tag == "influence":
		influence_loaded.emit(data)
		return

	if tag == "stats":
		vote_stats_loaded.emit(data)
		return

	if tag == "fetch":
		script_loaded.emit(data.get("script", {}))
		return

	if tag == "health":
		health_loaded.emit(data)
		return

	if tag == "weather":
		weather_loaded.emit(data)
		return

	if tag == "latest_news":
		latest_news_loaded.emit(data)
		return

	if tag == "script_list":
		script_list_loaded.emit(data.get("scripts", []))
		return

	if tag == "retention":
		retention_result.emit(data)
		return

	if data is Dictionary and data.has("script"):
		script_loaded.emit(data["script"])
	elif data is Dictionary and data.has("lines"):
		_download_audio_lines(data["lines"])
	elif data is Dictionary and data.has("scripts"):
		news_loaded.emit(data["scripts"])
	else:
		script_failed.emit("Unexpected server response: %s" % str(data))


func _download_audio_lines(lines: Array) -> void:
	for entry in lines:
		var audio_url: String = entry.get("audio_url", "")
		_download_audio(int(entry.get("index", 0)), audio_url)


func _download_audio(line_index: int, url: String) -> void:
	var downloader := HTTPRequest.new()
	add_child(downloader)
	downloader.request_completed.connect(
		func(_r: int, _c: int, _h: PackedStringArray, body: PackedByteArray) -> void:
			var audio := AudioStreamWAV.new()
			audio.load_from_buffer(body)
			if cache != null and _current_script_id != "":
				cache.cache_audio(_current_script_id, line_index, body)
			audio_ready.emit(line_index, audio)
			downloader.queue_free()
	)
	downloader.request(url)


func set_offline(value: bool) -> void:
	if is_offline == value:
		return
	is_offline = value
	offline_status_changed.emit(is_offline)