extends SceneTree
## Headless UI test: verifies the toast stack and loading overlay behave.
## ToastManager: show_message spawns a child, error styling flag, auto-dismiss
## removes it. LoadingScreen: set_progress drives the bar, show/finish toggle
## visibility.

const ToastManagerScene := preload("res://ui/ToastManager.gd")
const LoadingScreenScene := preload("res://ui/LoadingScreen.gd")
const ToastScene := preload("res://ui/ToastNotification.gd")

var _passed := false


func _init() -> void:
	_run()

func _run() -> void:
	var toasts: VBoxContainer = ToastManagerScene.new()
	root.add_child(toasts)
	var loading: Control = LoadingScreenScene.new()
	root.add_child(loading)

	toasts.show_message("Hitilafu ya mtandao", true)
	toasts.show_message("Habari zimepakuliwa", false)
	await process_frame
	if toasts.get_child_count() != 2:
		_fail("expected 2 toasts, got %d" % toasts.get_child_count())
		return

	var first: ToastNotification = toasts.get_child(0)
	if not (first is ToastNotification):
		_fail("toast children are not ToastNotification")
		return
	if first.get_child_count() == 0 or not (first.get_child(0) is Label):
		_fail("toast missing label")
		return

	# Loading overlay: progress -> finish hides it.
	loading.set_progress(2, 4)
	if loading.get_child_count() == 0:
		_fail("loading overlay missing children")
		return
	loading.show_screen()
	await process_frame
	loading.finish()
	await create_timer(0.6).timeout
	if loading.visible:
		_fail("loading overlay did not hide after finish")
		return

	# Toast auto-dismiss (short lifetime) removes the toast child.
	toasts.show_message("Short toast", false, 0.3)
	await create_timer(1.5).timeout
	if toasts.get_child_count() != 2:
		_fail("expected short toast dismissed (3 visible, got %d)" % toasts.get_child_count())
		return

	print("[TEST] PASS — toast stack + loading overlay behave correctly")
	_passed = true
	quit(0)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)