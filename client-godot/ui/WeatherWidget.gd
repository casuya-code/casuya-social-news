extends Label
## Weather sync widget (Features #14/#30). Renders the current sky the drama
## engine is writing under: condition, time of day, and the mood bias it
## applies to the cast. Falls back to a neutral line when unavailable.
##
## Single responsibility: payload -> human-readable Swahili status line.

const CONDITION_LABELS := {
	"mawingu": "Mawingu",
	"mvua": "Mvua",
	"dhoruba": "Dhoruba",
	"joto": "Joto",
	"baridi": "Baridi",
	"angavu": "Angavu",
	"hewa_safi": "Hewa safi",
}

const PERIOD_LABELS := {
	"asubuhi": "Asubuhi",
	"mchana": "Mchana",
	"usiku": "Usiku",
}

## Map the payload from GET /api/v1/weather to a status line.
func show_weather(payload: Dictionary) -> void:
	var condition := String(payload.get("condition", ""))
	var period := String(payload.get("time_of_day", ""))
	var mood: float = float(payload.get("mood_offset", 0.0))
	var location := String(payload.get("location", "Dar es Salaam"))
	var condition_text: String = String(CONDITION_LABELS.get(condition, condition))
	var period_text: String = String(PERIOD_LABELS.get(period, period))
	var mood_text := _mood_text(mood)
	text = "%s — %s, %s. %s" % [location, condition_text, period_text, mood_text]


## Neutral fallback when weather is unknown (offline / before first fetch).
func show_unknown() -> void:
	text = ""


## Private: mood offset -> friendly Swahili phrase.
func _mood_text(mood: float) -> String:
	if mood <= -0.3:
		return "Hisia chini — anga likifadhaisha wahusika"
	if mood < 0.0:
		return "Hisia kidogo chini — anga limezitoa"
	if mood == 0.0:
		return "Hisia za kawaida"
	if mood < 0.2:
		return "Hisia kidogo juu — anga linachangamsha"
	return "Hisia juu — anga linawasha wahusika"