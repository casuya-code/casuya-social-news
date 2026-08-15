class_name ToastNotification
extends PanelContainer
## A single non-blocking toast message. Auto-dismisses after a duration with a
## fade-out; emits `dismissed` when fully gone so the manager can clean up.

signal dismissed

const ERROR_BG := Color(0.45, 0.16, 0.16, 0.95)
const INFO_BG := Color(0.1, 0.25, 0.18, 0.95)

var _label: Label
var _fade_duration := 0.35
var _lifetime := 5.0
var _elapsed := 0.0
var _fading := false


func _init(message: String, is_error: bool = false) -> void:
	custom_minimum_size = Vector2(0, 40)
	var background := StyleBoxFlat.new()
	background.bg_color = ERROR_BG if is_error else INFO_BG
	background.corner_radius_top_left = 10
	background.corner_radius_top_right = 10
	background.corner_radius_bottom_left = 10
	background.corner_radius_bottom_right = 10
	background.content_margin_left = 16
	background.content_margin_right = 16
	background.content_margin_top = 8
	background.content_margin_bottom = 8
	add_theme_stylebox_override("panel", background)

	_label = Label.new()
	_label.text = message
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_label)


func _ready() -> void:
	modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(self, "modulate:a", 1.0, _fade_duration)


func _process(delta: float) -> void:
	if _fading:
		return
	_elapsed += delta
	if _elapsed >= _lifetime:
		_start_fade_out()


func _start_fade_out() -> void:
	_fading = true
	var tween := create_tween()
	tween.tween_property(self, "modulate:a", 0.0, _fade_duration)
	tween.tween_callback(_finish)


func _finish() -> void:
	dismissed.emit()
	queue_free()


func set_lifetime(seconds: float) -> void:
	_lifetime = seconds