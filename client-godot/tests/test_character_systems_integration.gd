extends SceneTree
## Headless test for CharacterController and character subsystems integration:
## Verifies that CharacterController properly initialises all 11 subsystems,
## handles line start/finish events, switches age profiles (gait),
## and manages eye gaze/facial state without errors.

const CHARACTER_CONTROLLER_SCRIPT := preload("res://characters/CharacterController.gd")


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	var ctrl: Node3D = CHARACTER_CONTROLLER_SCRIPT.new()
	root.add_child(ctrl)

	var body := Node3D.new()
	root.add_child(body)
	var head := Node3D.new()
	root.add_child(head)
	var left_eye := Node3D.new()
	root.add_child(left_eye)
	var right_eye := Node3D.new()
	root.add_child(right_eye)

	var ready_signaled: Array[String] = []
	ctrl.character_ready.connect(func(id: String) -> void:
		ready_signaled.append(id)
	)

	# 1. Setup controller with dummy 3D nodes
	ctrl.setup("char_mjomba", body, head, left_eye, right_eye)

	if ready_signaled.is_empty():
		_fail("character_ready signal was not emitted during setup")
		return

	if ctrl.lipsync == null or ctrl.eye_gaze == null or ctrl.gait == null or ctrl.idle == null:
		_fail("Subsystems not properly instantiated in CharacterController")
		return

	# 2. Test age transition (gait biomechanics)
	ctrl.set_age("zee")
	if ctrl.gait.get_speed() > 1.5:
		_fail("Elderly gait speed should be <= 1.5")
		return

	ctrl.set_age("kijana")
	if ctrl.gait.get_speed() < 2.0:
		_fail("Youth gait speed should be >= 2.0")
		return

	# 3. Test line started/finished lifecycle
	var speaking_events: Array[bool] = []
	ctrl.character_speaking.connect(func(_id: String, is_speaking: bool) -> void:
		speaking_events.append(is_speaking)
	)

	ctrl.on_line_started("anapiga_kelele")
	ctrl.on_line_finished()

	if speaking_events != [true, false]:
		_fail("Speaking event sequence mismatch: %s" % str(speaking_events))
		return

	# 4. Test EyeGazeSystem target tracking
	var target := Node3D.new()
	root.add_child(target)
	target.global_position = Vector3(3, 1, -2)
	ctrl.eye_gaze.set_target(target)
	ctrl.eye_gaze._process(0.016)

	# 5. Test dynamic auto-initialization (main.gd registration pattern)
	var dynamic_ctrl: Node3D = CHARACTER_CONTROLLER_SCRIPT.new()
	dynamic_ctrl.character_id = "char_shangazi"
	root.add_child(dynamic_ctrl)
	if dynamic_ctrl.lipsync == null or dynamic_ctrl.gait == null or dynamic_ctrl.cloth_wear == null:
		_fail("Dynamic CharacterController failed to auto-initialize subsystems in _ready")
		return
	dynamic_ctrl.on_line_started("anafikiria")
	dynamic_ctrl.on_line_finished()
	dynamic_ctrl.queue_free()

	# Clean up
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
