"""Talon code for Finder support."""
# Disable linter warnings caused by Talon conventions.
# pylint: disable=no-self-argument, no-method-argument, relative-beyond-top-level
# pyright: reportSelfClsParameterName=false, reportGeneralTypeIssues=false
# mypy: ignore-errors

from talon import Context, Module, actions
from talon.mac import applescript

mod = Module()
ctx = Context()

mod.apps.finder = """
os: mac
and app.bundle: com.apple.finder
"""

ctx.matches = r"""
app: finder
"""


@mod.action_class
class Actions:
  """Finder actions."""

  def finder_terminal_here():
    """Open a terminal in the same folder as the current Finder window."""
    # Try in iTerm2 first.
    try:
      actions.user.switcher_focus("iTerm2")
      applescript.run(r"""
        tell application "Finder"
            set currentPath to POSIX path of (target of front window as alias)
        end tell

        tell application "iTerm"
            -- For new window instead of tab: create window with default profile
            tell current window
              create tab with default profile
            end tell
            tell the current session of the current window
                write text "cd '" & currentPath & "'"
            end tell
        end tell
      """)
      return
    except ValueError:
      pass

    # Fall back to Terminal.
    applescript.run(r"""
      tell application "Finder"
          set myWin to window 1
          set thePath to (quoted form of POSIX path of (target of myWin as alias))
          tell application "Terminal"
              activate
              tell window 1
                  do script "cd " & thePath
              end tell
          end tell
      end tell""")


@ctx.action_class("user")
class ExtensionActions:
  """Action overwrites."""

  def file_manager_open_parent():
    actions.key("cmd-up")

  def file_manager_open_directory(path: str):
    actions.key("cmd-shift-g")
    actions.sleep("50ms")
    actions.insert(path)
    actions.key("enter")

  def tab_list(name: str):
    actions.key("cmd-shift-\\")
    actions.sleep("250ms")
    if name:
      actions.key("cmd-f")
      actions.insert(name)
      actions.sleep("50ms")
