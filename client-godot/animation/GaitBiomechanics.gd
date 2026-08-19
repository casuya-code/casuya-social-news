class_name GaitBiomechanics
extends Node
## Feature #19: Age -> Walk (Biomechanical Gait).
##
## Adjusts locomotion parameters (speed, stride, posture) based on a
## character's age descriptor. Older characters walk slower with shorter
## strides and more stooped posture; younger characters are springier.
## The age descriptor is a human-readable string (e.g., "kijana", "mtu mzima").

const GAIT_PROFILES := {
	"mtoto": {"speed": 1.8, "stride": 0.4, "stoop": 0.0, "bounce": 0.04},
	"kijana": {"speed": 2.5, "stride": 0.65, "stoop": 0.0, "bounce": 0.02},
	"mtu mzima": {"speed": 2.0, "stride": 0.6, "stoop": 0.02, "bounce": 0.01},
	"zee": {"speed": 1.2, "stride": 0.35, "stoop": 0.08, "bounce": 0.0},
}

const DEFAULT_PROFILE := "mtu mzima"

var _age: String = DEFAULT_PROFILE
var _speed := 2.0
var _stride := 0.6
var _stoop := 0.02
var _bounce := 0.01
var _body: Node3D


func setup(body: Node3D) -> void:
	_body = body


func set_age(age: String) -> void:
	_age = age.to_lower()
	var profile: Dictionary = GAIT_PROFILES.get(_age, GAIT_PROFILES[DEFAULT_PROFILE])
	_speed = profile["speed"]
	_stride = profile["stride"]
	_stoop = profile["stoop"]
	_bounce = profile["bounce"]
	if _body != null:
		_body.rotation.x = _stoop


func get_speed() -> float:
	return _speed


func get_stride() -> float:
	return _stride


func get_stoop() -> float:
	return _stoop


func get_bounce() -> float:
	return _bounce


func get_age() -> String:
	return _age


## Apply biomechanical gait to a ProceduralLocomotion component.
func apply_to(locomotion: Node) -> void:
	if locomotion != null and locomotion.has_method("set_speed"):
		locomotion.set_speed(_speed)
		locomotion.set_stride(_stride)
