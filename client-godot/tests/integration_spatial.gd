extends SceneTree
## Headless integration test for spatial audio (Feature #32) + acoustic
## occlusion (Feature #33). No server needed — pure client-side DSP params.
## Verifies:
## - procedural_pan is deterministic and produces distinct positions
## - apply_to() sets player.pan to the character's slot
## - occlusion maps emotion tags to factors; louder/brighter for shouting,
##   muffled + echoed for whisper/flashback
## - apply_to() translates factor into volume_db / pitch_scale

const SPATIAL_SCRIPT := preload("res://audio/SpatialAudioManager.gd")
const OCCLUSION_SCRIPT := preload("res://audio/AcousticOcclusion.gd")

var _spatial: Node
var _occlusion: Node
var _player: AudioStreamPlayer3D


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame

	_spatial = SPATIAL_SCRIPT.new()
	root.add_child(_spatial)
	_occlusion = OCCLUSION_SCRIPT.new()
	root.add_child(_occlusion)
	_player = AudioStreamPlayer3D.new()
	root.add_child(_player)

	# --- Feature #32: spatial pan ---
	var pan_a: float = _spatial.procedural_pan("char_mjomba")
	var pan_a2: float = _spatial.procedural_pan("char_mjomba")
	var pan_b: float = _spatial.procedural_pan("char_shangazi")
	if not is_equal_approx(pan_a, pan_a2):
		_fail("procedural_pan is not deterministic: %f vs %f" % [pan_a, pan_a2])
		return
	if is_equal_approx(pan_a, pan_b):
		_fail("two different characters share the same pan slot (%f)" % pan_a)
		return
	if pan_a < -1.0 or pan_a > 1.0:
		_fail("pan out of range: %f" % pan_a)
		return

	var applied: float = _spatial.apply_to(_player, "char_mjomba")
	var expected_x: float = applied * SPATIAL_SCRIPT.PAN_SPREAD
	if not is_equal_approx(_player.position.x, expected_x):
		_fail("apply_to did not position player (expected x=%f, got %f)" % [expected_x, _player.position.x])
		return
	if not is_equal_approx(_player.panning_strength, 1.0):
		_fail("panning_strength not set to 1.0")
		return
	print("[TEST] spatial pan %s=%f x=%.1f vs %s=%f" % ["char_mjomba", pan_a, expected_x, "char_shangazi", pan_b])

	# --- Feature #33: occlusion ---
	var shout: float = _occlusion.factor_for_emotion("anapiga_kelele")
	var whisper: float = _occlusion.factor_for_emotion("anafikiria")
	var calm: float = _occlusion.factor_for_emotion("anaongea_kwa_utulivu")
	if not (shout < calm and calm < whisper):
		_fail("occlusion ordering wrong: shout=%f calm=%f whisper=%f" % [shout, calm, whisper])
		return

	# Whisper must be quieter and lower pitched than a shout.
	_player.volume_db = 0.0
	_player.pitch_scale = 1.0
	_occlusion.apply_to(_player, "char_mjomba", "anafikiria")
	var whisper_db: float = _player.volume_db
	var whisper_pitch: float = _player.pitch_scale

	_player.volume_db = 0.0
	_player.pitch_scale = 1.0
	_occlusion.apply_to(_player, "char_mjomba", "anapiga_kelele")
	if not (_player.volume_db > whisper_db):
		_fail("shout volume_db should be higher than whisper: shout=%f whisper=%f" % [_player.volume_db, whisper_db])
		return
	if not (_player.pitch_scale > whisper_pitch):
		_fail("shout pitch should be higher than whisper: shout=%f whisper=%f" % [_player.pitch_scale, whisper_pitch])
		return

	var echo_whisper: float = _occlusion.echo_amount(whisper)
	var echo_shout: float = _occlusion.echo_amount(shout)
	if not (echo_whisper > echo_shout):
		_fail("whisper should carry more echo than shout")
		return

	print("[TEST] occlusion shout=%f db=%.1f | whisper=%f db=%.1f pitch=%.2f echo=%.2f" % [
		shout, shout * -14.0, whisper, whisper_db, whisper_pitch, echo_whisper,
	])
	print("[TEST] PASS — spatial pan + acoustic occlusion behave correctly")
	quit(0)


func _fail(message: String) -> void:
	print("[TEST] FAIL — ", message)
	quit(1)