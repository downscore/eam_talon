tag: browser
-
go input: user.browser_focus_address()
reload: user.browser_reload()
tab private: user.browser_open_private_tab()
bookmarks: user.browser_bookmarks()
bookmark add: user.browser_add_bookmark()

# Add the current tab URL to the Context section of the open Obsidian doc and close the tab.
tab context: user.browser_add_tab_to_context_and_close()
