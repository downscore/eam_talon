# Changing focus.
app <user.running_applications>: user.switcher_focus_app_by_name(running_applications)
app last: key(cmd-tab)

# Lists of applications.
app list running: user.switcher_toggle_running()
app list launch: user.switcher_toggle_launch()
app list launch next: user.switcher_launch_next_page()
app list launch last: user.switcher_launch_previous_page()

# Launching applications.
app launch <user.launch_applications>: user.switcher_launch(launch_applications)
# Shortcut for launching activity monitor.
activity monitor: user.switcher_launch("/System/Applications/Utilities/Activity Monitor.app")

# Close the current application (not just the window).
app terminate: user.switcher_close_running_app()

# Saving windows for shortcuts.
app save coder: user.switcher_save_current_window_by_name("coder")
app save browser: user.switcher_save_current_window_by_name("browser")
app save terminal: user.switcher_save_current_window_by_name("terminal")

# Shortcuts to apps.
obsidian: user.switcher_focus_app_by_name("Obsidian")
chit chat: user.switcher_focus_app_by_name("ChatGPT")
coder: user.switcher_focus_coder()
browser: user.switcher_focus_browser()
terminal: user.switcher_focus_terminal()
hangouts: user.switcher_focus_app_by_name("Google Chat")
finder: user.switcher_focus_app_by_name("Finder")

# Global shortcuts for opening a new terminal tab.
terminal new: user.switcher_new_tmux_window()
terminal here: user.switcher_new_tmux_window(user.app_get_current_directory())
terminal paste: user.switcher_new_tmux_window(clip.text())

# Global shortcuts for IDE bookmarks.
jump <user.number_small>: user.switcher_jump_to_bookmark(user.number_small)
