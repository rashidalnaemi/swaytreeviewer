import argparse
import sys
import signal
import gi
import i3ipc
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from gui import TreeVisualizer
from ipc import SwayListener

def main():
    """Main entry point for the Sway Tree Visualizer application."""
    # Parse command line arguments for display mode
    parser = argparse.ArgumentParser(description="Sway Tree Visualizer")
    parser.add_argument("--mode", choices=["window", "floating", "transparent", "fullscreen-transparent"], 
                        default="window", help="Display mode")
    args = parser.parse_args()

    # Create and configure the main application window
    app = TreeVisualizer(mode=args.mode)
    app.connect("destroy", Gtk.main_quit)  # Handle window close event
    app.show_all()  # Make all widgets visible

    # For floating/transparent modes, force the window to be floating in Sway
    # This ensures proper positioning and behavior
    if args.mode in ["floating", "transparent"]:
        def force_floating():
            """Force window to be floating via Sway IPC command."""
            try:
                conn = i3ipc.Connection()
                conn.command('[title="SwayTreeViewer"] floating enable')
            except Exception as e:
                print(f"Failed to force floating via IPC: {e}")
            return False  # Don't repeat this timeout

        # Delay the floating enforcement to ensure window is created first
        GLib.timeout_add(200, force_floating)

    def update_ui(tree, focused_ws_name):
        """Update the GUI with new tree data from the main GTK thread."""
        app.update_tree(tree, focused_ws_name)
        return False  # Return False to stop the idle function (it's a one-off call)

    def on_tree_change(tree, focused_ws_name):
        """Callback handler for tree changes - schedules UI update on main thread."""
        # Schedule the update on the main GTK thread to avoid threading issues
        GLib.idle_add(update_ui, tree, focused_ws_name)

    # Start Sway event listener in a separate thread to avoid blocking the GUI
    listener = SwayListener(callback=on_tree_change)
    listener.start()

    # Restore default Ctrl+C behavior for graceful shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        # Start the GTK main event loop
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up the listener thread on exit
        listener.stop()

if __name__ == "__main__":
    main()
