"""Client for VS Code Command Server extension. Adds Talon actions for using the command server."""
# Disable linter warnings caused by Talon conventions.
# pylint: disable=no-self-argument, no-method-argument, relative-beyond-top-level
# pyright: reportSelfClsParameterName=false, reportGeneralTypeIssues=false
# mypy: ignore-errors

import json
import os
from pathlib import Path
from tempfile import gettempdir
import time
from typing import Any, Dict, Optional
from uuid import uuid4
from talon import Context, Module, actions, speech_system

ctx = Context()
mod = Module()

ctx.matches = r"""
app: vscode
"""

# Indicates whether a pre-phrase signal was emitted for the current phrase.
_did_emit_pre_phrase_signal = False


def _get_ipc_path() -> Path:
  """Returns directory used by the Command Server extension for IPC."""
  # Add user ID to path if available on this OS.
  suffix = ""
  if hasattr(os, "getuid"):
    suffix = f"-{os.getuid()}"
  return Path(gettempdir()) / f"vscode-command-server{suffix}"


def _write_json_exclusive(path: Path, body: Any):
  """Writes object to file as JSON, failing if the file already exists."""
  with path.open("x") as out_file:
    out_file.write(json.dumps(body))


def _handle_existing_request_file(path):
  """If there is an existing request file, raises an exception if it was made recently or deletes it
  otherwise."""
  # How old a request file needs to be before we declare it stale and are willing to remove it
  stale_timeout_ms = 60_000

  stats = path.stat()

  modified_time_ms = stats.st_mtime_ns / 1e6
  current_time_ms = time.time() * 1e3
  time_difference_ms = abs(modified_time_ms - current_time_ms)

  if time_difference_ms < stale_timeout_ms:
    raise FileExistsError(f"Found recent request file. Age: {time_difference_ms} ms, Path: {path}")

  print(f"Removing stale VS Code Command Server request file. Path: {path}")
  path.unlink(missing_ok=True)


def _write_request(request: Dict[str, Any], path: Path):
  """Write the Command Server request file. Raises Exception if another process has recently written
  a file or we cannot exclusively open the file."""
  try:
    _write_json_exclusive(path, request)
    request_file_exists = False
  except FileExistsError:
    request_file_exists = True

  if request_file_exists:
    _handle_existing_request_file(path)
    _write_json_exclusive(path, request)


def _read_json_with_timeout(path: Path) -> Dict[str, Any]:
  """Repeatedly tries to read JSON from the given file path. Looks for a trailing new line to
  indicate that the write is complete. Returns the decoded file contents. Raises an exception if we
  timeout waiting for a result."""
  # The amount of time to wait for the response file to be available.
  command_timeout_seconds = 3.0

  # Minimum amount of time to wait when checking file. Also used as initial wait time.
  min_sleep_seconds = 0.0005

  timeout_time = time.perf_counter() + command_timeout_seconds
  sleep_time = min_sleep_seconds
  while True:
    try:
      raw_text = path.read_text()

      if raw_text.endswith("\n"):
        break
    except FileNotFoundError:
      # If not found, keep waiting
      pass

    actions.sleep(sleep_time)

    time_left = timeout_time - time.perf_counter()

    if time_left < 0:
      raise TimeoutError("Timed out waiting for VS Code Command Server response")

    # Use exponential backoff (or remaining time if smaller) with a minimum wait time.
    sleep_time = max(min(sleep_time * 2, time_left), min_sleep_seconds)

  return json.loads(raw_text)


def _get_prephrase_signal_path() -> Optional[Path]:
  """Gets the path to the prephrase signal in the signal subdirectory. Returns None if the IPC
  directory does not exist."""
  ipc_path = _get_ipc_path()

  if not ipc_path.exists():
    return None

  # Create the signal subdirectory if necessary.
  signal_dir = ipc_path / "signals"
  signal_dir.mkdir(parents=True, exist_ok=True)

  return signal_dir / "prePhrase"


def run_command(
    command_id: str,
    *args: Any,
    wait_for_finish: bool = False,
    return_command_output: bool = False,
):
  """Runs a command using the VS Code Command Server.
    Function args correspond to fields in the Command Server Request JSON. Returns the command
    output if requested.
    """
  # Convert variable args tuple to a list for use in the dict that will be serialized to JSON.
  args_list = [arg for arg in args if arg is not None]

  # Make sure the IPC path exists. It should be created by the Command Server Extension.
  ipc_path = _get_ipc_path()
  if not ipc_path.exists():
    raise FileNotFoundError(f"Command Server directory not found: {ipc_path}")
  request_path = ipc_path / "request.json"
  response_path = ipc_path / "response.json"

  # Pick random ID for the command.
  uuid = str(uuid4())

  # Make dict with request params.
  request_dict = {
      "commandId": command_id,
      "args": args_list,
      "waitForFinish": wait_for_finish,
      "returnCommandOutput": return_command_output,
      "uuid": uuid,
  }

  # The response file should not exist. Clear it if it does.
  if response_path.exists():
    print(f"Clearing old VS Code Command Server response file. Path: {response_path}")
    response_path.unlink(missing_ok=True)

  # Write the request, requiring exclusive access to the file.
  _write_request(request_dict, request_path)

  # Send keystroke triggering command execution. Keystrokes will only be sent to active VS Code
  # window.
  actions.user.vscode_trigger_command_server()

  try:
    decoded_contents = _read_json_with_timeout(response_path)
  finally:
    # Remove response file first. Once the request file is removed, another process can get
    # exclusive access to it.
    response_path.unlink(missing_ok=True)
    request_path.unlink(missing_ok=True)

  if decoded_contents["uuid"] != uuid:
    raise ValueError("UUIDs did not match in VS Code Command Server response")

  # Print any warnings in the response.
  for warning in decoded_contents["warnings"]:
    print(f"VS Code Command Server Warning: {warning}")

  # Raise error if present in the response.
  if decoded_contents["error"] is not None:
    raise ValueError(decoded_contents["error"])

  return decoded_contents["returnValue"]


@mod.action_class
class Actions:
  """VS Code Command Server action declarations and default implementations."""

  def vscode_trigger_command_server():
    """Sends keystrokes that trigger the VS Code Command Server extension to check for a request
    file."""
    actions.key("cmd-shift-f17")

  def emit_pre_phrase_signal() -> bool:
    """If VS Code is active, touches a file indicating a phrase is beginning and returns True."""
    # Default implementation just returns False.
    return False

  def did_emit_pre_phrase_signal() -> bool:
    """Indicates whether the pre-phrase signal was emitted at the start of this phrase."""
    return _did_emit_pre_phrase_signal

  def vscode(command_id: str,
             arg1: Any = None,
             arg2: Any = None,
             arg3: Any = None,
             arg4: Any = None):
    """Executes a command via VS Code Command Server."""
    # Default implementation (VS Code not active) throws an exception.
    raise RuntimeError(
        f"Tried running VS Code command when VS Code not active. Command: {command_id}")

  def vscode_and_wait(command_id: str,
                      arg1: Any = None,
                      arg2: Any = None,
                      arg3: Any = None,
                      arg4: Any = None):
    """Executes a command via VS Code Command Server and waits for it to finish."""
    # Default implementation (VS Code not active) throws an exception.
    raise RuntimeError(
        f"Tried running (wait) VS Code command when VS Code not active. Command: {command_id}")

  def vscode_return_value(command_id: str,
                          arg1: Any = None,
                          arg2: Any = None,
                          arg3: Any = None,
                          arg4: Any = None) -> Any:
    """Executes a command via VS Code Command Server and returns its return value."""
    # Default implementation (VS Code not active) throws an exception.
    raise RuntimeError(
        f"Tried running (return) VS Code command when VS Code not active. Command: {command_id}")


@ctx.action_class("user")
class UserActions:
  """Action implementations when VS Code is active."""

  def emit_pre_phrase_signal():
    signal_path = _get_prephrase_signal_path()
    if signal_path is None:
      return False
    signal_path.touch()
    return True

  def vscode(command_id: str,
             arg1: Any = None,
             arg2: Any = None,
             arg3: Any = None,
             arg4: Any = None):
    run_command(command_id, arg1, arg2, arg3, arg4)

  def vscode_and_wait(command_id: str,
                      arg1: Any = None,
                      arg2: Any = None,
                      arg3: Any = None,
                      arg4: Any = None):
    run_command(command_id, arg1, arg2, arg3, arg4, wait_for_finish=True)

  def vscode_return_value(command_id: str,
                          arg1: Any = None,
                          arg2: Any = None,
                          arg3: Any = None,
                          arg4: Any = None) -> Any:
    return run_command(command_id, arg1, arg2, arg3, arg4, return_command_output=True)


def pre_phrase(_: Any):
  global _did_emit_pre_phrase_signal
  _did_emit_pre_phrase_signal = actions.user.emit_pre_phrase_signal()


def post_phrase(_: Any):
  global _did_emit_pre_phrase_signal
  _did_emit_pre_phrase_signal = False


speech_system.register("pre:phrase", pre_phrase)
speech_system.register("post:phrase", post_phrase)
