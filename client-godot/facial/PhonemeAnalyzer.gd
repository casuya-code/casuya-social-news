class_name PhonemeAnalyzer
extends RefCounted
## Feature #8: Dynamic Phoneme Extraction.
##
## Analyses an AudioStreamSample to detect volume peaks and silences that
## approximate phoneme boundaries for a lipsync system. Works with any sample
## rate — normalises internally. Returns an array of {time, phoneme} dicts
## sorted by timestamp.

const PHONEME_MAP := {
	"silence": "X",
	"vowel_open": "A",
	"vowel_mid": "E",
	"vowel_close": "I",
	"consonant_plosive": "P",
	"consonant_fricative": "S",
}

const WINDOW_SAMPLES := 512


## Analyse the given audio and return an array of {time: float, phoneme: String}
## dicts approximating phoneme boundaries.
func analyse(stream: AudioStream) -> Array:
	if stream == null or not stream is AudioStreamWAV:
		return []
	var sample: AudioStreamWAV = stream
	var data := sample.data
	if data.size() == 0:
		return []

	var frames := data.size() / (2 if sample.format == AudioStreamWAV.FORMAT_16_BITS else 1)
	var step := int(WINDOW_SAMPLES)
	var results: Array = []
	var prev_energy := 0.0
	var prev_phoneme := "silence"

	for i in range(0, frames, step):
		var energy := _window_energy(data, i, step, sample.format)
		var time := float(i) / float(sample.mix_rate)
		var phoneme := _classify_energy(energy)
		if phoneme != prev_phoneme or absf(energy - prev_energy) > 0.3:
			results.append({"time": time, "phoneme": phoneme})
			prev_phoneme = phoneme
		prev_energy = energy
	return results


func _window_energy(data: PackedByteArray, offset: int, length: int, format: int) -> float:
	var sum := 0.0
	var count := 0
	var limit := mini(offset + length, data.size())
	for i in range(offset, limit):
		if format == AudioStreamWAV.FORMAT_16_BITS and i + 1 < data.size():
			var raw := data[i] | (data[i + 1] << 8)
			# Sign-extend from 16-bit unsigned to signed.
			var sample_val := raw if raw < 32768 else raw - 65536
			sum += absf(float(sample_val) / 32768.0)
			count += 1
		elif format == AudioStreamWAV.FORMAT_8_BITS:
			var sample_val_8 := data[i] if data[i] < 128 else data[i] - 256
			sum += absf(float(sample_val_8) / 128.0)
			count += 1
	if count == 0:
		return 0.0
	return sum / float(count)


func _classify_energy(energy: float) -> String:
	if energy < 0.05:
		return "silence"
	if energy < 0.15:
		return "consonant_fricative"
	if energy < 0.35:
		return "vowel_close"
	if energy < 0.55:
		return "vowel_mid"
	if energy < 0.75:
		return "vowel_open"
	return "consonant_plosive"
