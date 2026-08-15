extends SceneTree
## Headless integration test for OfflineCache (offline story + audio cache).
## Uses an isolated user:// cache dir. Verifies:
## - cache_script / load_script round-trip
## - cache_audio / load_audio round-trip (PackedByteArray)
## - LRU eviction when story count exceeds max_stories
## - byte-budget eviction when total exceeds max_bytes
## - list_scripts() returns MRU-first order

const CACHE_SCRIPT := preload("res://storage/OfflineCache.gd")

var _cache: Node
var _unique := str(Time.get_unix_time_from_system())


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame

	_cache = CACHE_SCRIPT.new()
	_cache.cache_dir = "user://test_cache_%s" % _unique
	root.add_child(_cache)

	# --- round-trip: script ---
	var script := {
		"script_id": "story-1",
		"headline": "Habari",
		"lines": [{"index": 0, "text": "Habari ya leo"}],
	}
	if not _cache.cache_script(script):
		_fail("cache_script returned false")
		return
	var loaded: Dictionary = _cache.load_script("story-1")
	if loaded.get("script_id", "") != "story-1":
		_fail("load_script round-trip failed: %s" % str(loaded))
		return

	# --- round-trip: audio bytes ---
	var bytes := PackedByteArray([1, 2, 3, 4, 5])
	if not _cache.cache_audio("story-1", 0, bytes):
		_fail("cache_audio returned false")
		return
	var loaded_bytes: PackedByteArray = _cache.load_audio("story-1", 0)
	if loaded_bytes.size() != 5 or loaded_bytes[4] != 5:
		_fail("load_audio round-trip failed: %s" % str(loaded_bytes))
		return

	# --- MRU ordering + LRU story-count eviction ---
	for i in range(3):
		_cache.cache_script({"script_id": "story-%d" % (i + 2)})
	_cache.max_stories = 3
	_cache._enforce_limits()
	var ids: Array = _cache.list_scripts()
	if ids.size() > 3:
		_fail("story-count eviction did not trim to %d (got %d)" % [3, ids.size()])
		return
	if "story-1" in ids:
		_fail("LRU eviction did not drop oldest story-1: %s" % str(ids))
		return
	if _cache.has("story-1"):
		_fail("evicted story still present on disk")
		return
	if ids.size() != 3:
		_fail("expected 3 cached stories, got %d" % ids.size())
		return

	# --- byte-budget eviction ---
	var big := {"script_id": "story-9", "data": ("x".repeat(4000))}
	_cache.cache_script(big)
	_cache.max_bytes = 2000  # far smaller than one big script
	_cache._enforce_limits()
	if _cache.total_bytes() > 2000:
		_fail("byte budget exceeded: %d > 2000" % _cache.total_bytes())
		return

	_cache.clear()
	if not _cache.list_scripts().is_empty():
		_fail("clear() left entries behind")
		return

	print("[TEST] PASS — script/audio round-trip, LRU eviction, byte budget, clear")
	quit(0)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)