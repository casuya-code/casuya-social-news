class_name OfflineCache
extends Node
## Offline story + audio cache.
##
## Persists the last N scripts and their synthesized audio bytes to disk under
## `user://`, bounded by a byte budget (default 100 MB). Access is tracked so
## the least-recently-used entry is evicted first when either limit is hit.
## Used by the client's offline mode so listeners can replay cached stories
## without a connection.

signal entry_evicted(script_id: String)

const DEFAULT_MAX_STORIES := 10
const DEFAULT_MAX_BYTES := 100 * 1024 * 1024  # 100 MB

var max_stories := DEFAULT_MAX_STORIES
var max_bytes := DEFAULT_MAX_BYTES
var cache_dir := "user://offline_cache"

var _manifest: Dictionary = {}  # script_id -> {last_used, bytes, audio: {line: bytes}}
var _dirty := false


func _ready() -> void:
	_ensure_dir()
	_load_manifest()


## Store a full script. Returns true on success.
func cache_script(script: Dictionary) -> bool:
	var script_id: String = script.get("script_id", "")
	if script_id == "":
		return false
	_ensure_dir()
	var path := _path_for(script_id)
	var json := JSON.stringify(script)
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(json)
	file.close()

	var entry: Dictionary = _manifest.get(script_id, {})
	entry["audio"] = entry.get("audio", {})
	entry["bytes"] = json.length()
	entry["last_used"] = Time.get_unix_time_from_system()
	_manifest[script_id] = entry
	_mark_dirty()
	_enforce_limits()
	return true


## Store audio bytes for one line of a cached script. Returns true on success.
func cache_audio(script_id: String, line_index: int, bytes: PackedByteArray) -> bool:
	if not _manifest.has(script_id):
		return false
	_ensure_dir()
	var path := _audio_path_for(script_id, line_index)
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_buffer(bytes)
	file.close()

	var entry: Dictionary = _manifest[script_id]
	var audio: Dictionary = entry.get("audio", {})
	var delta := int(bytes.size()) - int(audio.get(str(line_index), 0))
	audio[str(line_index)] = bytes.size()
	entry["audio"] = audio
	entry["bytes"] = int(entry.get("bytes", 0)) + delta
	entry["last_used"] = Time.get_unix_time_from_system()
	_mark_dirty()
	_enforce_limits()
	return true


func has(script_id: String) -> bool:
	return _manifest.has(script_id)


## Load a cached script back (or {} when missing).
func load_script(script_id: String) -> Dictionary:
	if not _manifest.has(script_id):
		return {}
	var file := FileAccess.open(_path_for(script_id), FileAccess.READ)
	if file == null:
		return {}
	var parsed := JSON.new()
	if parsed.parse(file.get_as_text()) != OK:
		return {}
	_touch(script_id)
	return parsed.data


## Load cached audio bytes for a line (or an empty array).
func load_audio(script_id: String, line_index: int) -> PackedByteArray:
	if not _manifest.has(script_id):
		return PackedByteArray()
	var path := _audio_path_for(script_id, line_index)
	if not FileAccess.file_exists(path):
		return PackedByteArray()
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return PackedByteArray()
	_touch(script_id)
	return file.get_buffer(file.get_length())


## Cached script ids, most-recently-used first.
func list_scripts() -> Array:
	var ids: Array = _manifest.keys()
	ids.sort_custom(func(a: String, b: String) -> bool:
		return _manifest[a]["last_used"] > _manifest[b]["last_used"]
	)
	return ids


func total_bytes() -> int:
	var total := 0
	for script_id in _manifest:
		total += int(_manifest[script_id].get("bytes", 0))
	return total


func clear() -> void:
	_manifest.clear()
	var dir := DirAccess.open(cache_dir)
	if dir != null:
		for f in dir.get_files():
			dir.remove(f)
	_mark_dirty()
	_save_manifest()


## Evict entries until within story count and byte budget.
func _enforce_limits() -> void:
	while _manifest.size() > max_stories or total_bytes() > max_bytes:
		var victim := _least_recent()
		if victim == "":
			return
		_evict(victim)
	if _dirty:
		_save_manifest()


func _evict(script_id: String) -> void:
	var entry: Dictionary = _manifest[script_id]
	var audio: Dictionary = entry.get("audio", {})
	var dir := DirAccess.open(cache_dir)
	if dir != null:
		for line in audio:
			var fname := "%s__line%s.audio" % [script_id, line]
			if dir.file_exists(fname):
				dir.remove(fname)
		if dir.file_exists(script_id + ".json"):
			dir.remove(script_id + ".json")
	_manifest.erase(script_id)
	entry_evicted.emit(script_id)
	_mark_dirty()


func _least_recent() -> String:
	var victim := ""
	var oldest := INF
	for script_id in _manifest:
		var used: float = _manifest[script_id].get("last_used", 0.0)
		if used < oldest:
			oldest = used
			victim = script_id
	return victim


func _touch(script_id: String) -> void:
	if not _manifest.has(script_id):
		return
	_manifest[script_id]["last_used"] = Time.get_unix_time_from_system()
	_mark_dirty()
	_save_manifest()


func _path_for(script_id: String) -> String:
	return "%s/%s.json" % [cache_dir, script_id]


func _audio_path_for(script_id: String, line_index: int) -> String:
	return "%s/%s__line%d.audio" % [cache_dir, script_id, line_index]


func _ensure_dir() -> void:
	var dir := DirAccess.open("user://")
	if dir != null and not dir.dir_exists(cache_dir):
		dir.make_dir_recursive(cache_dir)


func _mark_dirty() -> void:
	_dirty = true


func _load_manifest() -> void:
	var path := "%s/manifest.json" % cache_dir
	if not FileAccess.file_exists(path):
		return
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return
	var parsed := JSON.new()
	if parsed.parse(file.get_as_text()) == OK and parsed.data is Dictionary:
		_manifest = parsed.data
	# Drop entries whose files no longer exist.
	for script_id in _manifest.keys():
		if not FileAccess.file_exists(_path_for(script_id)):
			_manifest.erase(script_id)


func _save_manifest() -> void:
	_ensure_dir()
	var file := FileAccess.open("%s/manifest.json" % cache_dir, FileAccess.WRITE)
	if file == null:
		return
	file.store_string(JSON.stringify(_manifest))
	file.close()
	_dirty = false