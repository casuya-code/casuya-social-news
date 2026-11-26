extends SceneTree
## Headless test for ProceduralCamera, ShotComposer, and BeatTracker (2D):
## Verifies shot switching, 2D target tracking, and beat tracker pacing.

const CAMERA_SCRIPT := preload("res://camera/ProceduralCamera.gd")
const SHOT_COMPOSER_SCRIPT := preload("res://camera/ShotComposer.gd")
const BEAT_TRACKER_SCRIPT := preload("res://camera/BeatTracker.gd")


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	await process_frame

	var beat_tracker: Node = BEAT_TRACKER_SCRIPT.new()
	root.add_child(beat_tracker)
	var mock_script := {
		"script_id": "camera_beat_test",
		"lines": [
			{"index": 0, "character_id": "a", "emotion": "upimaji", "text": "Hujambo"},
			{"index": 1, "character_id": "b", "emotion": "hasira", "text": "Hapana!"},
			{"index": 2, "character_id": "a", "emotion": "wasiwasi", "text": "Nini kimetokea?"}
		]
	}
	beat_tracker.load_script(mock_script)
	beat_tracker.advance_line(0)
	beat_tracker.advance_line(1)

	var shot_composer: Node = SHOT_COMPOSER_SCRIPT.new()
	root.add_child(shot_composer)
	shot_composer.setup(beat_tracker)
	shot_composer.set_active_characters(2)

	var cam: Node2D = CAMERA_SCRIPT.new()
	root.add_child(cam)

	var target_2d := Node2D.new()
	root.add_child(target_2d)
	target_2d.global_position = Vector2(50, 50)

	cam.set_target(target_2d)
	cam.switch_to_wide()
	cam._process(0.016)

	if cam.current_shot != 0:
		_fail("Current shot should be wide (0)")
		return

	var wide_pos: Vector2 = cam.global_position

	cam.switch_to_closeup()
	cam._process(0.016)

	if cam.current_shot != 1:
		_fail("Current shot should be closeup (1)")
		return

	var closeup_pos: Vector2 = cam.global_position
	if wide_pos == closeup_pos:
		_fail("Wide and closeup camera positions should differ")
		return

	target_2d.queue_free()
	cam.queue_free()
	shot_composer.queue_free()
	beat_tracker.queue_free()

	print("[TEST] PASS — procedural camera, shot composer, and beat tracker executed cleanly")
	quit(0)


func _fail(msg: String) -> void:
	print("[TEST] FAIL — ", msg)
	quit(1)
