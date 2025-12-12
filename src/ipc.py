import threading
import i3ipc
import time

class SwayListener(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.connection = None
        self.running = True
        self.daemon = True  # Ensure thread dies when main app dies

    def run(self):
        try:
            self.connection = i3ipc.Connection()
        except Exception as e:
            print(f"Failed to connect to Sway: {e}")
            return

        # Subscribe to relevant events
        self.connection.on('window', self.on_event)
        self.connection.on('workspace', self.on_event)

        # Initial fetch
        self.refresh_tree()

        # Start the event loop
        self.connection.main()

    def on_event(self, i3, event):
        self.refresh_tree()

    def refresh_tree(self):
        if not self.connection:
            return
        try:
            tree = self.connection.get_tree()
            # We also need to know the focused workspace to filter the tree
            workspaces = self.connection.get_workspaces()
            focused_ws = next((ws for ws in workspaces if ws.focused), None)
            
            if focused_ws:
                self.callback(tree, focused_ws.name)
        except Exception as e:
            print(f"Error refreshing tree: {e}")

    def stop(self):
        if self.connection:
            self.connection.main_quit()
