extends Node
## NetworkManager — single autoload for all server communication.
## Attach as an autoload named "Network" in Project Settings.
##
## Responsibilities:
##  - Fetch a script (news -> dialogue) from the server
##  - Fetch/synthesize audio for each line
##  - Offline detection and queued retries (Feature: OfflineDetector)

signal script_loaded(script: Dictionary)
signal news_loaded(scripts: Array)
signal script_failed(message: String)
signal audio_ready(line_index: int, audio: AudioStream)
signal offline_status_changed(is_offline: bool)

const DEFAULT_BASE_URL := "http://127.0.0.1:8000"
const API_PREFIX := "/api/v1"
const DEFAULT_API_KEY := "dev-api-key"

var base_url: String = DEFAULT_BASE_URL
var api_key: String = DEFAULT_API_KEY
var is_offline := false

var _http: HTTPRequest
var _pending: Array[Dictionary] = []
var _max_retries := 3
var _retry_delay_s := 1.0


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)


## Generate a script from a news headline.
func generate_script(headline: String, source: String, url: String) -> void:
	var body := JSON.stringify({
		"headline": headline,
		"source": source,
		"url": url,
	})
	var headers := _auth_headers(true)
	var err := _http.request(
		base_url + API_PREFIX + "/scripts/generate",
		headers,
		HTTPClient.METHOD_POST,
		body
	)
	if err != OK:
		script_failed.emit("Request failed to start (code %d)" % err)


## Synthesize audio for every line of a script.
func generate_audio(script: Dictionary) -> void:
	var body := JSON.stringify({"script": script})
	var headers := _auth_headers(true)
	var err := _http.request(
		base_url + API_PREFIX + "/scripts/generate-audio",
		headers,
		HTTPClient.METHOD_POST,
		body
	)
	if err != OK:
		script_failed.emit("Audio request failed to start (code %d)" % err)


## Pull fresh news and generate a script for each new story ("endless loop").
func refresh_news() -> void:
	var headers := _auth_headers(false)
	var err := _http.request(
		base_url + API_PREFIX + "/news/refresh",
		headers,
		HTTPClient.METHOD_POST
	)
	if err != OK:
		script_failed.emit("News refresh failed to start (code %d)" % err)


func _auth_headers(is_json: bool) -> PackedStringArray:
	var headers := PackedStringArray()
	headers.append("X-API-Key: %s" % api_key)
	if is_json:
		headers.append("Content-Type: application/json")
	return headers


func _on_request_completed(result: int, _code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		script_failed.emit("Network error: %d" % result)
		return

	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		script_failed.emit("Malformed JSON from server")
		return

	var envelope: Dictionary = json.data
	if not envelope.get("success", false):
		script_failed.emit(envelope.get("message", "Unknown server error"))
		return

	var data: Variant = envelope.get("data")
	if data is Dictionary and data.has("script"):
		script_loaded.emit(data["script"])
	elif data is Dictionary and data.has("lines"):
		_download_audio_lines(data["lines"])
	elif data is Dictionary and data.has("scripts"):
		news_loaded.emit(data["scripts"])


func _download_audio_lines(lines: Array) -> void:
	for entry in lines:
		var audio_url: String = entry.get("audio_url", "")
		_download_audio(int(entry.get("index", 0)), audio_url)


func _download_audio(line_index: int, url: String) -> void:
	var downloader := HTTPRequest.new()
	add_child(downloader)
	downloader.request_completed.connect(
		func(_r: int, _c: int, _h: PackedStringArray, body: PackedByteArray) -> void:
			var audio := AudioStreamWAV.create_from_wav_bytes(body)
			audio_ready.emit(line_index, audio)
			downloader.queue_free()
	)
	downloader.request(url)


func set_offline(value: bool) -> void:
	if is_offline == value:
		return
	is_offline = value
	offline_status_changed.emit(is_offline)