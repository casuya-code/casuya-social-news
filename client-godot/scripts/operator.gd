extends Control
## Operator console — health, scheduler, recent scripts, retention triggers.
## Opened from the main scene; everything reads from the same /api/v1 surface
## the browser console uses (health, scripts list, maintenance/retention).

@onready var status_label: Label = %OpStatusLabel
@onready var db_label: Label = %OpDbLabel
@onready var cache_label: Label = %OpCacheLabel
@onready var tts_label: Label = %OpTtsLabel
@onready var sched_label: Label = %OpSchedLabel
@onready var circuit_label: Label = %OpCircuitLabel
@onready var scripts_box: VBoxContainer = %OpScriptsBox
@onready var close_button: Button = %OpCloseButton
@onready var retention_button: Button = %OpRetentionButton
@onready var dry_run_button: Button = %OpDryRunButton

var _health: Dictionary = {}


func _ready() -> void:
	Network.health_loaded.connect(_on_health_loaded)
	Network.script_list_loaded.connect(_on_script_list_loaded)
	Network.retention_result.connect(_on_retention_result)
	close_button.pressed.connect(_close)
	retention_button.pressed.connect(func() -> void: Network.run_retention(false))
	dry_run_button.pressed.connect(func() -> void: Network.run_retention(true))
	_refresh_all()


func _refresh_all() -> void:
	status_label.text = "Inapakia..."
	Network.fetch_health()
	Network.fetch_script_list(10)


func _on_health_loaded(payload: Dictionary) -> void:
	_health = payload
	var overall: String = payload.get("status", "unknown")
	status_label.text = "Hali: %s" % overall
	db_label.text = _dep_text(payload, "database")
	cache_label.text = _dep_text(payload, "cache")
	tts_label.text = _dep_text(payload, "tts")
	var sched: Dictionary = payload.get("scheduler", {})
	var running: String = "washa" if sched.get("running", false) else "zima"
	sched_label.text = "Scheduler: %s | mizunguko %d | hadithi %d | usafishaji %d" % [
		running,
		sched.get("cycles_completed", 0),
		sched.get("stories_generated", 0),
		sched.get("retention_runs", 0),
	]
	var circuit: Dictionary = payload.get("circuit", {})
	circuit_label.text = "Mzunguko wa TTS: %s" % circuit.get("state", "unknown")


func _dep_text(payload: Dictionary, key: String) -> String:
	var deps: Dictionary = payload.get("dependencies", {})
	var value: String = deps.get(key, "unknown")
	var label := "DB" if key == "database" else ("Cache" if key == "cache" else "TTS")
	return "%s: %s" % [label, value]


func _on_script_list_loaded(scripts: Array) -> void:
	for child in scripts_box.get_children():
		child.queue_free()
	if scripts.is_empty():
		_add_script_row("Hakuna hadithi bado")
		return
	for script in scripts:
		var headline: String = script.get("headline", "")
		var line_count: int = script.get("line_count", 0)
		_add_script_row("%s  (%d mistari)" % [headline, line_count])


func _add_script_row(text: String) -> void:
	var row := Label.new()
	row.text = text
	row.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	row.add_theme_color_override("font_color", Color(0.6, 0.72, 0.95, 1))
	scripts_box.add_child(row)


func _on_retention_result(payload: Dictionary) -> void:
	var audio: Dictionary = payload.get("audio", {})
	var dry_run: bool = payload.get("dry_run", false)
	var prefix := "Uchambuzi (dry-run): " if dry_run else "Usafishaji: "
	status_label.text = "%s sauti %d | makala %d | scripts %d" % [
		prefix,
		audio.get("purged", 0),
		payload.get("articles_deleted", 0),
		payload.get("scripts_compressed", 0),
	]
	# Refresh the health panel so retention_runs reflects the sweep.
	Network.fetch_health()


func _close() -> void:
	Network.health_loaded.disconnect(_on_health_loaded)
	Network.script_list_loaded.disconnect(_on_script_list_loaded)
	Network.retention_result.disconnect(_on_retention_result)
	queue_free()