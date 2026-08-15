class_name RetryHandler
extends RefCounted
## Backoff retry policy for transport-level request failures.
##
## Given a request tag, tracks how many times it has been retried and computes
## the next delay. Only transport failures (HTTPRequest result != SUCCESS) are
## retryable; server-side errors (envelope `success: false`) are surfaced to the
## caller immediately because retrying them won't help.

signal retry_scheduled(tag: String, attempt: int, delay_s: float)

var max_retries := 3
var base_delay_s := 1.0
var backoff_factor := 2.0

var _attempts: Dictionary = {}  # tag -> int


## Register a failure for `tag`. Returns true when the failure should be retried
## (attempts remain), false when it must be surfaced to the caller.
func register_failure(tag: String) -> bool:
	var attempt: int = _attempts.get(tag, 0) + 1
	_attempts[tag] = attempt
	if attempt > max_retries:
		return false
	var delay := base_delay_s * pow(backoff_factor, attempt - 1)
	retry_scheduled.emit(tag, attempt, delay)
	return true


## Exponential backoff delay for the current attempt of `tag`.
func delay_for(tag: String) -> float:
	var attempt: int = _attempts.get(tag, 1)
	return base_delay_s * pow(backoff_factor, attempt - 1)


func attempts_for(tag: String) -> int:
	return _attempts.get(tag, 0)


func reset(tag: String = "") -> void:
	if tag == "":
		_attempts.clear()
	else:
		_attempts.erase(tag)