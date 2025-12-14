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
    
    # 0. CONNECT TO IPC EARLY (Before GUI creation)
    # capture the ID of the currently focused window immediately
    previous_focus_id = None
    try:
        ipc = i3ipc.Connection()
        tree = ipc.get_tree()
        focused_node = tree.find_focused()
        if focused_node:
            previous_focus_id = focused_node.id
        
        # 1. TOGGLE CHECK
        # Search for an existing instance of our application
        # We search by title since we set it in gui.py
        existing = tree.find_named("SwayTreeViewer")
        
        if existing:
            # If we find one, we assume the user wants to close it (Toggle behavior)
            for node in existing:
                node.command('kill')
            sys.exit(0)

        # PREVENT FOCUS STEALING
        # Tell Sway explicitly NOT to focus this specific process's window when it appears.
        # This is more reliable than restoring focus afterwards.
        ipc.command(f'for_window [pid={os.getpid()}] no_focus')
            
    except Exception as e:
        print(f"IPC Initialization Warning: {e}")

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
        args.width = "100%" 
    if args.height is None:
        args.height = "100%"
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

    # 2. RESTORE FOCUS (Delayed)
    # Use GLib.timeout_add to restore focus AFTER the window manager has processed the 'show' event.
    # This mitigates race conditions where the WM steals focus back immediately after we restore it.
    def restore_focus_delayed():
        if previous_focus_id:
            try:
                # Create a fresh connection for the thread/callback
                r_ipc = i3ipc.Connection()
                r_ipc.command(f'[con_id={previous_focus_id}] focus')
                r_ipc.main_quit()
            except Exception as e:
                print(f"Failed to restore focus: {e}")
        return False # Stop the timeout function from repeating

    # Run after 50ms (adjust if still racy, but 50-100ms is usually sufficient)
    GLib.timeout_add(50, restore_focus_delayed)

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
