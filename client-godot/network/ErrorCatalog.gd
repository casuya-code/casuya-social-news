class_name ErrorCatalog
## Error code UX — maps the server's machine-readable error codes
## (E0000–E5002, see shared/docs/data_contract.md) to friendly Swahili
## messages for the UI, and flags which codes are transient (worth a retry).
##
## Single responsibility: turn error_code into (message, transient).


## Friendly user-facing text for an error code. Falls back to the raw server
## message, then to a generic "Hitilafu (code)" string.
static func describe(code: String, fallback: String = "") -> String:
	match code:
		"E0000":
			return "Hitilafu isiyojulikana ya seva"
		"E1001":
			return "Maombi hayakubaliki — utengenezaji wa hadithi umeshindwa"
		"E1002":
			return "Uchanganuzi wa hisia umeshindwa"
		"E1003":
			return "Utengenezaji wa hadithi ulichukua muda mrefu"
		"E2001":
			return "Mtoa sauti (TTS) umeshindwa"
		"E2002":
			return "Kikomo cha bajeti ya sauti (TTS) kimefikiwa"
		"E2003":
			return "Uandishi wa faili la sauti umeshindwa"
		"E3001":
			return "Kitu kilichoombwa hakikupatikana"
		"E3002":
			return "Hifadhidata haifikiki"
		"E3003":
			return "Hifadhidata inahitaji sasisho (toleo la schema)"
		"E4001":
			return "Ufunguo au tokeni si sahihi"
		"E4002":
			return "Kikao kimeisha (tokeni imeisha muda)"
		"E4003":
			return "Umeomba mara nyingi sana — subiri kidogo"
		"E5001":
			return "Chanzo cha habari hakipatikani — tumetumia akiba"
		"E5002":
			return "Chanzo cha habari kimepunguza kasi — tumetumia akiba"
		_:
			if fallback != "":
				return fallback
			return "Hitilafu (code: %s)" % code


## True when the code describes a temporary condition where a later retry
## may succeed (timeouts, quotas, rate limits, offline feeds).
static func is_transient(code: String) -> bool:
	return code in ["E1003", "E2002", "E3002", "E4003", "E5001", "E5002"]


## Short Swahili label for operator/status UI.
static func label(code: String) -> String:
	match code:
		"E0000":
			return "Seva"
		"E1001":
			return "Maombi"
		"E1002":
			return "Hisia"
		"E1003":
			return "Muda"
		"E2001":
			return "Sauti"
		"E2002":
			return "Bajeti sauti"
		"E2003":
			return "Faili sauti"
		"E3001":
			return "Hakuna"
		"E3002":
			return "Hifadhidata"
		"E3003":
			return "Hifadhidata"
		"E4001":
			return "Uthibitisho"
		"E4002":
			return "Kikao"
		"E4003":
			return "Kiwango"
		"E5001":
			return "Habari"
		"E5002":
			return "Habari"
		_:
			return code