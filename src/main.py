import sys
import signal
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from gui import TreeVisualizer
from ipc import SwayListener

def main():
    app = TreeVisualizer()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()

    def update_ui(tree, focused_ws_name):
        app.update_tree(tree, focused_ws_name)
        return False # Return False to stop the idle function (it's a one-off call)

    def on_tree_change(tree, focused_ws_name):
        # Schedule the update on the main GTK thread
        GLib.idle_add(update_ui, tree, focused_ws_name)

    # Start Sway listener in a separate thread
    listener = SwayListener(callback=on_tree_change)
    listener.start()

    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()

if __name__ == "__main__":
    main()
