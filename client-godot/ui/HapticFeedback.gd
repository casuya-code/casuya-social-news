class_name HapticFeedback
extends Node
## Provides haptic feedback on mobile devices for key interactions.
## Falls back gracefully on desktop (no-op).

enum HapticType { LIGHT, MEDIUM, HEAVY, SUCCESS, WARNING, ERROR }


## Trigger haptic feedback of the given type. No-op on platforms without vibration.
func trigger(haptic_type: HapticType = HapticType.LIGHT) -> void:
	if not OS.has_feature("mobile") and not OS.has_feature("android") and not OS.has_feature("ios"):
		return
	match haptic_type:
		HapticType.LIGHT:
			_vibrate(10)
		HapticType.MEDIUM:
			_vibrate(25)
		HapticType.HEAVY:
			_vibrate(50)
		HapticType.SUCCESS:
			_vibrate(15)
		HapticType.WARNING:
			_vibrate(30)
		HapticType.ERROR:
			_vibrate(40)


func _vibrate(duration_ms: int) -> void:
	if Input.vibrate_handheld(duration_ms):
		return
	# Fallback for older Godot versions
	Input.vibrate_handheld(duration_ms / 1000.0)
