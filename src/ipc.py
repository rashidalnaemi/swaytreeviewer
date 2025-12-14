import threading

import i3ipc


class SwayListener(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.connection = None
        self.stop_event = threading.Event()
        self.daemon = True

    def run(self):
        # Start Event Listener
        try:
            self.connection = i3ipc.Connection()
            self.connection.on("window", self.on_event)
            self.connection.on("workspace", self.on_event)
            self.connection.on("binding", self.on_event)
            # self.connection.on('mode', self.on_event) # Potential extra event

            # Initial fetch
            self.refresh_tree(self.connection)

            self.connection.main()
        except Exception as e:
            print(f"Event listener failed: {e}")

    def on_event(self, i3, event):
        self.refresh_tree(self.connection)

    def refresh_tree(self, conn):
        if not conn:
            return
        try:
            tree = conn.get_tree()
            workspaces = conn.get_workspaces()
            focused_ws = next((ws for ws in workspaces if ws.focused), None)

            if focused_ws:
                self.callback(tree, focused_ws.name)
        except Exception as e:
            # Connection might be closed or broken
            pass

    def stop(self):
        self.stop_event.set()
        if self.connection:
            self.connection.main_quit()
