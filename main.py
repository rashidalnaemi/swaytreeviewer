import argparse
import sys
import os
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
    parser.add_argument("--mode", choices=["window", "transparent"],
                        default="window", help="Display mode")
    parser.add_argument("--include-floating", action="store_true",
                        help="Include floating windows in the visualization")
    parser.add_argument("--alpha", type=float, default=None,
                        help="Opacity of the visualization (0.0 - 1.0). Useful for transparent mode.")
    parser.add_argument("--width", type=str, default=None,
                        help="Initial width of the window (pixels or %%)")
    parser.add_argument("--height", type=str, default=None,
                        help="Initial height of the window (pixels or %%)")
    args = parser.parse_args()

    # Set defaults based on mode if not provided
    if args.width is None:
        args.width = "100%" if args.mode == "transparent" else "500"
    if args.height is None:
        args.height = "100%" if args.mode == "transparent" else "400"
    if args.alpha is None:
        args.alpha = 0.5 if args.mode == "transparent" else 1.0

    # For transparent mode, set up floating rule before creating window
    # This ensures it starts floating immediately (no tiling flicker)
    if args.mode == "transparent":
        try:
            conn = i3ipc.Connection()
            conn.command(f'for_window [pid={os.getpid()}] floating enable')
        except Exception as e:
            print(f"Failed to set floating rule via IPC: {e}")

    # Create and configure the main application window
    app = TreeVisualizer(mode=args.mode, include_floating=args.include_floating, alpha=args.alpha, width=args.width, height=args.height)
    app.connect("destroy", Gtk.main_quit)  # Handle window close event
    app.show_all()  # Make all widgets visible

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
