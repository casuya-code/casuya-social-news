class_name AppSettings
extends RefCounted
## Client settings (Feature: Settings) — audio quality, notifications, data
## saving. Persisted to user:// via ConfigFile and surfaced through typed
## accessors + a single `changed` signal so the UI and runtime can react.

signal changed

## Overridable so tests can isolate their config file.
var settings_path := "user://settings.cfg"
const SECTION := "client"

enum AudioQuality { LOW, HIGH }

var _quality := AudioQuality.HIGH
var _notifications := true
var _data_saving := false

var _config := ConfigFile.new()


## Load settings from disk. Safe to call any time (creates defaults if absent).
func load_settings() -> void:
	_config.load(settings_path)
	_quality = int(_config.get_value(SECTION, "audio_quality", AudioQuality.HIGH))
	_notifications = bool(_config.get_value(SECTION, "notifications", true))
	_data_saving = bool(_config.get_value(SECTION, "data_saving", false))


func save_settings() -> void:
	_config.set_value(SECTION, "audio_quality", _quality)
	_config.set_value(SECTION, "notifications", _notifications)
	_config.set_value(SECTION, "data_saving", _data_saving)
	_config.save(settings_path)


func set_quality(quality: int) -> void:
	if quality != _quality:
		_quality = quality
		changed.emit()


func get_quality() -> int:
	return _quality


func is_high_quality() -> bool:
	return _quality == AudioQuality.HIGH


## TTS quality parameter sent to the server (Feature: data saving).
func quality_param() -> String:
	return "high" if is_high_quality() else "low"


func set_notifications(enabled: bool) -> void:
	if enabled != _notifications:
		_notifications = enabled
		changed.emit()


func notifications_enabled() -> bool:
	return _notifications


func set_data_saving(enabled: bool) -> void:
	if enabled != _data_saving:
		_data_saving = enabled
		changed.emit()


func data_saving_enabled() -> bool:
	return _data_saving