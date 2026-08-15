class_name LoadingScreen
extends Control
## Full-screen dim overlay shown while audio is being synthesized.
## `set_status(text)` updates the caption; `set_progress(done, total)` drives
## the bar; `finish()` fades the overlay out.

var _overlay: ColorRect
var _progress: ProgressBar
var _status: Label
var _fade_duration := 0.25


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	modulate.a = 0.0
	visible = false

	_overlay = ColorRect.new()
	_overlay.color = Color(0, 0, 0, 0.6)
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_overlay)

	var center := VBoxContainer.new()
	center.set_anchors_preset(Control.PRESET_CENTER)
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(center)

	_status = Label.new()
	_status.text = "Inaandaa sauti..."
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	center.add_child(_status)

	_progress = ProgressBar.new()
	_progress.min_value = 0
	_progress.max_value = 1
	_progress.value = 0
	_progress.custom_minimum_size = Vector2(220, 16)
	center.add_child(_progress)


func set_status(text: String) -> void:
	_status.text = text


func set_progress(done: int, total: int) -> void:
	if total <= 0:
		_progress.value = 0
		return
	_progress.max_value = float(total)
	_progress.value = float(done)
	_status.text = "Sauti: %d / %d" % [done, total]


func show_screen() -> void:
	visible = true
	modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(self, "modulate:a", 1.0, _fade_duration)


func finish() -> void:
	var tween := create_tween()
	tween.tween_property(self, "modulate:a", 0.0, _fade_duration)
	tween.tween_callback(_hide_now)


func _hide_now() -> void:
	visible = false