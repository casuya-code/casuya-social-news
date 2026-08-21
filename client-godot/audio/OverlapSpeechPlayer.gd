class_name OverlapSpeechPlayer
extends Node
## Feature #6 (client side): plays script lines with talk-over. Lines flagged
## `overlap: true` (heated scenes) begin before the previous line finishes,
## using a second AudioStreamPlayer, so characters genuinely talk over each
## other. Non-overlapping lines play strictly sequentially.
##
## Uses AudioStreamPlayer (not 3D) for proper audio in a Control (2D) scene.
## Panning is applied via Audio buses.

signal line_started(index: int)
signal sequence_finished

const OVERLAP_LEAD_S := 0.35  ## how early an overlapping line starts (before prev ends)

var _players: Array[AudioStreamPlayer] = []
var _active_player := 0
var _lines: Array = []
var _audio: Dictionary = {}  # index -> AudioStream
var _index := -1
var _playing := false
var _seq := 0


func _ready() -> void:
	for i in 2:
		var player := AudioStreamPlayer.new()
		player.bus = "Master"
		add_child(player)
		_players.append(player)
		player.finished.connect(func() -> void: _on_player_finished(i))


## Start playing `lines` (drama line dicts with an `overlap` flag) using the
## given `audio` map (line index -> AudioStream). Overlapping lines start just
## before their predecessor finishes on the second player.
func play(lines: Array, audio: Dictionary) -> void:
	stop()
	_lines = lines
	_audio = audio
	_index = 0
	_playing = true
	_start_line(0)


## Skip straight to the next line (used by spacebar).
func skip() -> void:
	if not _playing or _index < 0:
		return
	_seq += 1
	_stop_players()
	_index += 1
	if _index >= _lines.size():
		_finish_sequence()
		return
	_start_line(_index)


func stop() -> void:
	_seq += 1
	_playing = false
	_index = -1
	_stop_players()


func is_playing() -> bool:
	return _playing


func _start_line(index: int) -> void:
	_index = index
	line_started.emit(index)

	var stream: AudioStream = _audio.get(index)
	if stream == null:
		_next_line()
		return

	var overlaps_prev: bool = index > 0 and _lines[index].get("overlap", false)
	if overlaps_prev:
		# Cut in over the previous line's tail on the other player.
		_play_on((_active_player + 1) % 2, stream)
	else:
		_stop_players()
		_play_on(_active_player, stream)

	var delay := stream.get_length() - (OVERLAP_LEAD_S if _line_overlaps_next(index) else 0.0)
	if delay < 0.0:
		delay = 0.0
	var my_seq := _seq
	_wait(delay, func() -> void:
		if _seq == my_seq and _playing:
			_next_line()
	)


## Whether the *following* line is marked to overlap this one.
func _line_overlaps_next(index: int) -> bool:
	return index + 1 < _lines.size() and _lines[index + 1].get("overlap", false)


func _next_line() -> void:
	if not _playing:
		return
	var next := _index + 1
	if next >= _lines.size():
		_finish_sequence()
		return
	_start_line(next)


func _finish_sequence() -> void:
	_seq += 1
	_playing = false
	_stop_players()
	sequence_finished.emit()


func _play_on(slot: int, stream: AudioStream) -> void:
	_players[slot].stop()
	_players[slot].stream = stream
	_players[slot].play()
	_active_player = slot


func _on_player_finished(slot: int) -> void:
	# When a player finishes naturally, if it was the active player and we
	# are not in overlap mode, advance to the next line. The timer-based
	# sequencing covers most cases, but this handles short clips that end
	# before the timer fires.
	if slot == _active_player and _playing and not is_talking_over():
		var stream: AudioStream = _audio.get(_index)
		if stream != null and stream.get_length() < 0.2:
			_next_line()


func _wait(seconds: float, callback: Callable) -> void:
	get_tree().create_timer(seconds).timeout.connect(
		func() -> void: callback.call()
	)


func _stop_players() -> void:
	for player in _players:
		player.stop()


func get_active_player_index() -> int:
	return _active_player


## The AudioStreamPlayer currently carrying this line's voice (for volume/pitch).
func get_active_player() -> AudioStreamPlayer:
	return _players[_active_player]


func is_talking_over() -> bool:
	# True while this line (marked overlap) is cutting into the previous tail.
	if _index < 0:
		return false
	return _lines[_index].get("overlap", false) and _players[(_active_player + 1) % 2].playing
