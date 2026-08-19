class_name CharacterController
extends Node3D
## Integration hub for all character subsystems. Wires together facial
## (lipsync, eye gaze, blink), animation (locomotion, idle, gestures),
## and appearance (texture swap, cloth wear) for a single character.
##
## Single responsibility: orchestrate character subsystems from a unified API.

signal character_ready(character_id: String)
signal character_speaking(character_id: String, is_speaking: bool)

const LipsyncControllerClass := preload("res://facial/LipsyncController.gd")
const EyeGazeSystemClass := preload("res://facial/EyeGazeSystem.gd")
const BlinkReflexClass := preload("res://facial/BlinkReflex.gd")
const CognitiveEyeDartClass := preload("res://facial/CognitiveEyeDart.gd")
const ProceduralLocomotionClass := preload("res://animation/ProceduralLocomotion.gd")
const IdleGeneratorClass := preload("res://animation/IdleGenerator.gd")
const GaitBiomechanicsClass := preload("res://animation/GaitBiomechanics.gd")
const CulturalGestureClass := preload("res://animation/CulturalGestures.gd")
const ProximityShaderClass := preload("res://animation/ProximityShader.gd")
const TextureSwapperClass := preload("res://characters/TextureSwapper.gd")
const ClothWearAlgorithmClass := preload("res://characters/ClothWearAlgorithm.gd")

var character_id: String = ""
var age: String = "mtu mzima"

var lipsync: Node
var eye_gaze: Node
var blink: Node
var cognitive_dart: Node
var locomotion: Node
var idle: Node
var gait: Node
var gestures: Node
var proximity: Node
var texture_swapper: Node
var cloth_wear: Node


func _ready() -> void:
	if lipsync == null:
		setup(character_id, self)


func setup(id: String, body: Node3D, head: Node3D = null, left_eye: Node3D = null, right_eye: Node3D = null, left_leg: SkeletonIK3D = null, right_leg: SkeletonIK3D = null, clothing_mat: Material = null, mesh: MeshInstance3D = null) -> void:
	character_id = id

	if lipsync == null:
		lipsync = LipsyncControllerClass.new()
		lipsync.name = "Lipsync"
		add_child(lipsync)

	if eye_gaze == null:
		eye_gaze = EyeGazeSystemClass.new()
		eye_gaze.name = "EyeGaze"
		add_child(eye_gaze)
	if left_eye != null and right_eye != null:
		eye_gaze.setup(id, left_eye, right_eye)

	if blink == null:
		blink = BlinkReflexClass.new()
		blink.name = "Blink"
		add_child(blink)
	if left_eye != null:
		blink.setup(id, left_eye)

	if cognitive_dart == null:
		cognitive_dart = CognitiveEyeDartClass.new()
		cognitive_dart.name = "CognitiveDart"
		add_child(cognitive_dart)
	if left_eye != null:
		cognitive_dart.setup(id, left_eye)

	if locomotion == null:
		locomotion = ProceduralLocomotionClass.new()
		locomotion.name = "Locomotion"
		add_child(locomotion)
	if left_leg != null and right_leg != null:
		locomotion.setup(id, body, left_leg, right_leg)

	if idle == null:
		idle = IdleGeneratorClass.new()
		idle.name = "Idle"
		add_child(idle)
	if body != null:
		idle.setup(id, body, head)

	if gait == null:
		gait = GaitBiomechanicsClass.new()
		gait.name = "Gait"
		add_child(gait)
	if body != null:
		gait.setup(body)
	gait.set_age(age)

	if gestures == null:
		gestures = CulturalGestureClass.new()
		gestures.name = "Gestures"
		add_child(gestures)

	if proximity == null:
		proximity = ProximityShaderClass.new()
		proximity.name = "Proximity"
		add_child(proximity)

	if texture_swapper == null:
		texture_swapper = TextureSwapperClass.new()
		texture_swapper.name = "TextureSwapper"
		add_child(texture_swapper)
	if mesh != null:
		texture_swapper.setup(id, mesh)

	if cloth_wear == null:
		cloth_wear = ClothWearAlgorithmClass.new()
		cloth_wear.name = "ClothWear"
		add_child(cloth_wear)
	if clothing_mat != null:
		cloth_wear.setup(id, clothing_mat)

	character_ready.emit(id)


func on_line_started(emotion: String) -> void:
	character_speaking.emit(character_id, true)
	if idle != null:
		idle.set_active(false)
	if cognitive_dart != null:
		cognitive_dart.set_active(emotion in ["anafikiria", "anahofia"])
	if cloth_wear != null:
		cloth_wear.set_active(true)
	if gestures != null:
		gestures.play_gesture(_gesture_for_emotion(emotion))


func on_line_finished() -> void:
	character_speaking.emit(character_id, false)
	if idle != null:
		idle.set_active(true)
	if cognitive_dart != null:
		cognitive_dart.set_active(false)
	if cloth_wear != null:
		cloth_wear.set_active(false)
	if gestures != null:
		gestures.stop()


func set_age(new_age: String) -> void:
	age = new_age
	if gait != null:
		gait.set_age(new_age)


func _gesture_for_emotion(emotion: String) -> String:
	match emotion:
		"anapiga_kelele", "anakasirika":
			return "emphasis"
		"anasikitika", "anaongea_kwa_huzuni":
			return "mourning"
		"anajigamba":
			return "praise"
		"anashangaa":
			return "welcome"
		_:
			return "emphasis"
