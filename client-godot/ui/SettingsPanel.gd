extends Control
## Settings panel — audio quality, notifications, data-saving toggle.
## Reads/writes a shared AppSettings instance, saving on close. Applied live:
## toggling data saving flips audio quality to low; quality changes set the
## server TTS parameter.

@onready var status_label: Label = %SetStatus
@onready var low_button: Button = %LowQualityButton
@onready var high_button: Button = %HighQualityButton
@onready var notifications_check: CheckButton = %NotificationsCheck
@onready var data_check: CheckButton = %DataCheck
@onready var close_button: Button = %SetCloseButton

var settings: AppSettings


func _ready() -> void:
	low_button.pressed.connect(func() -> void: settings.set_quality(AppSettings.AudioQuality.LOW))
	high_button.pressed.connect(func() -> void: settings.set_quality(AppSettings.AudioQuality.HIGH))
	notifications_check.toggled.connect(func(on: bool) -> void: settings.set_notifications(on))
	data_check.toggled.connect(func(on: bool) -> void: settings.set_data_saving(on))
	close_button.pressed.connect(_close)
	settings.changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	var data_saving := settings.data_saving_enabled()
	low_button.disabled = not settings.is_high_quality() or data_saving
	high_button.disabled = settings.is_high_quality() or data_saving
	notifications_check.set_pressed_no_signal(settings.notifications_enabled())
	data_check.set_pressed_no_signal(data_saving)
	status_label.text = "Ubora: %s" % ("Juu (128kbps)" if settings.is_high_quality() and not data_saving else "Chini (64kbps)")


func _close() -> void:
	settings.save_settings()
	queue_free()