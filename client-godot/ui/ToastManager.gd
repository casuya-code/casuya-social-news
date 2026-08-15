class_name ToastManager
extends VBoxContainer
## Non-blocking alert stack. `show_message(text, is_error)` drops a toast that
## auto-dismisses and removes itself; errors use a red background.

func _ready() -> void:
	alignment = BoxContainer.ALIGNMENT_BEGIN
	add_theme_constant_override("separation", 8)


func show_message(message: String, is_error: bool = false, lifetime: float = 5.0) -> void:
	var toast := ToastNotification.new(message, is_error)
	toast.set_lifetime(lifetime)
	toast.dismissed.connect(func() -> void: _on_dismissed(toast))
	add_child(toast)


func _on_dismissed(toast: ToastNotification) -> void:
	if is_instance_valid(toast) and toast.get_parent() == self:
		remove_child(toast)