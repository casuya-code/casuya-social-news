extends SceneTree
## Headless integration test for AppSettings + SettingsPanel (Feature:
## Settings). Uses an isolated user:// settings file. Verifies:
## - defaults (high quality, notifications on, data saving off)
## - setter round-trip + changed signal emission
## - persistence across load_settings()
## - data-saving forces low quality param
## - SettingsPanel binds its controls to a shared AppSettings

const SETTINGS_SCRIPT := preload("res://settings/AppSettings.gd")
const PANEL_SCRIPT := preload("res://scenes/settings.tscn")

var _settings: AppSettings
var _unique := str(Time.get_unix_time_from_system())
var _changed_count := 0


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame

	_settings = SETTINGS_SCRIPT.new()
	_settings.settings_path = "user://test_settings_%s.cfg" % _unique
	_settings.load_settings()

	# --- defaults ---
	if not _settings.is_high_quality():
		_fail("default quality should be HIGH")
		return
	if not _settings.notifications_enabled():
		_fail("default notifications should be on")
		return
	if _settings.data_saving_enabled():
		_fail("default data saving should be off")
		return

	# --- setters + change signal ---
	_settings.changed.connect(func() -> void: _changed_count += 1)
	_settings.set_quality(AppSettings.AudioQuality.LOW)
	_settings.set_notifications(false)
	_settings.set_data_saving(true)
	if _changed_count != 3:
		_fail("expected 3 changed signals, got %d" % _changed_count)
		return
	if _settings.is_high_quality():
		_fail("quality did not apply")
		return

	# --- data saving forces low quality param ---
	if _settings.quality_param() != "low":
		_fail("data-saving should force low quality param")
		return

	# --- persistence ---
	_settings.save_settings()
	var reloaded := SETTINGS_SCRIPT.new()
	reloaded.settings_path = "user://test_settings_%s.cfg" % _unique
	reloaded.load_settings()
	if reloaded.is_high_quality() or reloaded.notifications_enabled() or not reloaded.data_saving_enabled():
		_fail("persistence round-trip failed")
		return

	# --- SettingsPanel binds to shared settings ---
	var panel: Control = PANEL_SCRIPT.instantiate()
	panel.settings = _settings
	root.add_child(panel)
	await process_frame
	await process_frame
	var data_check: CheckButton = panel.get_node("%DataCheck")
	var high_button: Button = panel.get_node("%HighQualityButton")
	if not data_check.button_pressed:
		_fail("panel did not reflect data-saving=true")
		return
	if not high_button.disabled:
		_fail("panel should disable HIGH while data saving is active")
		return
	panel.queue_free()

	print("[TEST] PASS — settings defaults, signals, persistence, data-saving, panel binding")
	quit(0)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)