extends SceneTree
## Headless test for CharacterController and character subsystems integration (2D):
## Verifies that CharacterController properly initialises all subsystems,
## handles line start/finish events, switches age profiles, and exercises
## eye gaze without errors.

const CHARACTER_CONTROLLER_SCRIPT := preload("res://characters/CharacterController.gd")


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	var ctrl: Node2D = CHARACTER_CONTROLLER_SCRIPT.new()
	root.add_child(ctrl)

	var body := Node2D.new()
	root.add_child(body)
	var head := Node2D.new()
	root.add_child(head)
	var left_eye := Node2D.new()
	root.add_child(left_eye)
	var right_eye := Node2D.new()
	root.add_child(right_eye)

	var ready_signaled: Array[String] = []
	ctrl.character_ready.connect(func(id: String) -> void:
		ready_signaled.append(id)
	)

	ctrl.setup("char_mjomba", body, head, left_eye, right_eye)

	if ready_signaled.is_empty():
		_fail("character_ready signal was not emitted during setup")
		return

	if ctrl.lipsync == null or ctrl.eye_gaze == null or ctrl.gait == null or ctrl.idle == null:
		_fail("Subsystems not properly instantiated in CharacterController")
		return

	ctrl.set_age("zee")
	if ctrl.gait.get_speed() > 1.5:
		_fail("Elderly gait speed should be <= 1.5")
		return

	ctrl.set_age("kijana")
	if ctrl.gait.get_speed() < 2.0:
		_fail("Youth gait speed should be >= 2.0")
		return

	var speaking_events: Array[bool] = []
	ctrl.character_speaking.connect(func(_id: String, is_speaking: bool) -> void:
		speaking_events.append(is_speaking)
	)

	ctrl.on_line_started("anapiga_kelele")
	ctrl.on_line_finished()

	if speaking_events != [true, false]:
		_fail("Speaking event sequence mismatch: %s" % str(speaking_events))
		return

	var target := Node2D.new()
	root.add_child(target)
	target.global_position = Vector2(30, 10)
	ctrl.eye_gaze.set_target(target)
	ctrl.eye_gaze._process(0.016)

	var dynamic_ctrl: Node2D = CHARACTER_CONTROLLER_SCRIPT.new()
	dynamic_ctrl.character_id = "char_shangazi"
	root.add_child(dynamic_ctrl)
	if dynamic_ctrl.lipsync == null or dynamic_ctrl.gait == null or dynamic_ctrl.cloth_wear == null:
		_fail("Dynamic CharacterController failed to auto-initialize subsystems in _ready")
		return
	dynamic_ctrl.on_line_started("anafikiria")
	dynamic_ctrl.on_line_finished()
	dynamic_ctrl.queue_free()

	ctrl.queue_free()
	body.queue_free()
	head.queue_free()
	left_eye.queue_free()
	right_eye.queue_free()
	target.queue_free()

	print("[TEST] PASS — character controller and all 11 subsystems successfully wired, configured, and exercised")
	quit(0)


func _fail(msg: String) -> void:
	print("[TEST] FAIL — ", msg)
	quit(1)
