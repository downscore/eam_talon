"""Talon code for Chrome support."""
# Disable linter warnings caused by Talon conventions.
# pylint: disable=no-self-argument, no-method-argument, relative-beyond-top-level
# pyright: reportSelfClsParameterName=false, reportGeneralTypeIssues=false
# mypy: ignore-errors

import collections
import re
from talon import Context, Module, actions
from talon.mac import applescript
from ..core.lib import browser_util
from ..core.lib.textflow_match import get_phrase_regex

mod = Module()
ctx = Context()

mod.apps.chrome = "app.name: Google Chrome"
mod.apps.chrome = """
os: mac
and app.bundle: com.google.Chrome
"""
mod.apps.chrome = """
os: mac
and app.bundle: org.chromium.Chromium
"""

ctx.matches = r"""
app: chrome
"""


@ctx.action_class("browser")
class BrowserActions:
  """Browser action overwrites."""

  def address():
    return applescript.run("""
                tell application id "com.google.Chrome"
                    if not (exists (window 1)) then return ""
                    return window 1's active tab's URL
                end tell
            """)


@ctx.action_class("user")
class ExtensionActions:
  """Action overrides."""

  def browser_go(url: str):
    applescript.run("""
                tell application id "com.google.Chrome"
                    if not (exists (window 1)) then return
                    set window 1's active tab's URL to "[URL]"
                end tell
            """.replace("[URL]", url))

  def find():
    actions.key("cmd-f")
    # Add a brief pause so we don't swallow subsequent keystrokes before the find dialog opens.
    actions.sleep("100ms")

  def line_insert_down():
    actions.user.line_end()
    actions.key("shift-enter")

  def line_insert_up():
    # Going to line end first can help consistently preserve indentation in code.
    actions.user.line_end()
    actions.user.line_start()
    actions.key("shift-enter up")

  def tab_close():
    actions.key("cmd-w")

  def tab_next():
    actions.key("cmd-shift-]")

  def tab_open():
    actions.key("cmd-t")

  def tab_previous():
    actions.key("cmd-shift-a")
    actions.sleep("250ms")
    actions.key("enter")

  def tab_reopen():
    actions.key("cmd-shift-t")

  def tab_left():
    actions.key("cmd-shift-[")

  def tab_right():
    actions.key("cmd-shift-]")

  def tab_switch_by_index(num: int):
    actions.key(f"cmd-{num}")

  def tab_switch_by_name(name: str):
    # TODO: Implement in browser tag using browser_get_all_tabs and other actions.
    tab_delimiter = "|||"
    script = f'set my_delimiter to "{tab_delimiter}"\n\n'
    script += """
      on remove_delimiter_from_text(the_text, the_delimiter)
          set AppleScript's text item delimiters to the_delimiter
          set text_items to text items of the_text
          set AppleScript's text item delimiters to ""
          set the_text to text_items as text
          return the_text
      end remove_delimiter_from_text

      tell application id "com.google.Chrome"
          set currentWindow to front window
          set all_tabs to {}
          set tab_count to count of tabs in currentWindow
          repeat with j from 1 to tab_count
              set tab_url to url of tab j of currentWindow
              set tab_name to name of tab j of currentWindow
              set clean_url to my remove_delimiter_from_text(tab_url, my_delimiter)
              set clean_name to my remove_delimiter_from_text(tab_name, my_delimiter)
              set tab_info to {clean_url & my_delimiter & clean_name & my_delimiter}
              set end of all_tabs to tab_info
          end repeat
      end tell
      return all_tabs as text
      """
    tab_list_string = applescript.run(script)

    # Removed trailing delimiter from output, if present.
    if tab_list_string.endswith(tab_delimiter):
      tab_list_string = tab_list_string[:-len(tab_delimiter)]

    # Make a list of tabs.
    Tab = collections.namedtuple("Tab", ["name", "url"])
    tab_strings = tab_list_string.split(tab_delimiter)
    tabs: list[Tab] = []
    for i in range(0, len(tab_strings), 2):
      tabs.append(Tab(name=tab_strings[i + 1].strip(), url=tab_strings[i].strip()))

    # Prepare query regex.
    regex_str = get_phrase_regex(name.split(), actions.user.get_all_homophones)
    regex = re.compile(regex_str, re.IGNORECASE)

    # Find the tab with the given string as a substring of its name or URL.
    found_index = 0  # 1-based.
    for i, tab in enumerate(tabs):
      # Perform a case-insensitive search.
      if regex.search(tab.name) or regex.search(tab.url):
        found_index = i + 1
        break
    if found_index == 0:
      raise ValueError(f"Could not find tab. Name: {name}")

    # Switch to the tab.
    set_tab_script = f"""
        tell application id "com.google.Chrome"
            activate
            tell front window
                set active tab index to {found_index}
            end tell
        end tell
      """
    applescript.run(set_tab_script)

  def tab_list(name: str):
    actions.key("cmd-shift-a")
    actions.sleep("250ms")
    if name:
      actions.insert(name)
      actions.sleep("50ms")

  def browser_get_all_tabs() -> list[browser_util.Tab]:
    return actions.user.chrome_get_all_tabs()
