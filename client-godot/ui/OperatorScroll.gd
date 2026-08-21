extends ScrollContainer
## Scroll container for the operator panel content. Allows the health,
## scripts, and news sections to scroll on small screens where they
## would otherwise overflow off-screen.

func _ready() -> void:
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	follow_focus = true
