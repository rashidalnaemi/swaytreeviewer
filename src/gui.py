import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

class TreeVisualizer(Gtk.Window):
    def __init__(self):
        super().__init__(title="SwayTreeViewer")
        self.set_default_size(400, 300)
        self.set_keep_above(True) # Keep window on top
        
        # Make the window floating and sticky via hints (Sway config might still be needed)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)
        
        self.current_tree = None
        self.focused_workspace_name = None

    def update_tree(self, tree, focused_ws_name):
        self.current_tree = tree
        self.focused_workspace_name = focused_ws_name
        # Schedule redraw on main thread
        self.queue_draw()

    def on_draw(self, widget, ctx):
        if not self.current_tree or not self.focused_workspace_name:
            # Draw placeholder or clear
            ctx.set_source_rgb(0.1, 0.1, 0.1)
            ctx.paint()
            return

        # Find the active workspace node
        ws_node = None
        for output in self.current_tree.nodes:
             # Iterate to find content container, then workspaces
             if output.name == '__i3': continue
             for container in output.nodes: # content, dockarea...
                 if container.type == 'con': # Sometimes workspace is direct child? Depends on i3ipc version vs sway version.
                     # Traverse to find workspace
                     pass
        
        # Easier search: recursive find
        ws_node = self.find_node_by_name(self.current_tree, self.focused_workspace_name)

        if ws_node:
            # Background
            ctx.set_source_rgb(0.15, 0.15, 0.15)
            ctx.paint()
            
            # Calculate scaling
            w_width = widget.get_allocated_width()
            w_height = widget.get_allocated_height()
            
            # Workspace rect
            ws_rect = ws_node.rect
            
            scale_x = w_width / ws_rect.width if ws_rect.width else 1
            scale_y = w_height / ws_rect.height if ws_rect.height else 1
            scale = min(scale_x, scale_y) * 0.9 # 90% fill to leave margin
            
            offset_x = (w_width - (ws_rect.width * scale)) / 2
            offset_y = (w_height - (ws_rect.height * scale)) / 2
            
            ctx.translate(offset_x, offset_y)
            ctx.scale(scale, scale)
            
            # Reset origin relative to workspace for easier drawing
            ctx.translate(-ws_rect.x, -ws_rect.y)

            self.draw_node(ctx, ws_node)

    def find_node_by_name(self, node, name):
        if node.name == name and node.type == 'workspace':
            return node
        for child in node.nodes + node.floating_nodes:
            res = self.find_node_by_name(child, name)
            if res: return res
        return None

    def draw_node(self, ctx, node):
        # Draw current node
        r = node.rect
        
        # Skip workspace node background itself (or draw it as container)
        is_leaf = len(node.nodes) == 0
        
        # Colors
        if node.focused:
            ctx.set_source_rgb(0.2, 0.6, 1.0) # Blue highlight
            ctx.set_line_width(4)
        else:
            ctx.set_source_rgb(0.3, 0.3, 0.3) # Grey
            ctx.set_line_width(2)
            
        if is_leaf:
            # Fill leaf
            if node.focused:
                ctx.set_source_rgba(0.2, 0.6, 1.0, 0.4)
            else:
                ctx.set_source_rgba(0.3, 0.3, 0.3, 0.4)
            ctx.rectangle(r.x, r.y, r.width, r.height)
            ctx.fill_preserve()
            
            # Border
            if node.focused:
                 ctx.set_source_rgb(0.2, 0.6, 1.0)
            else:
                 ctx.set_source_rgb(0.5, 0.5, 0.5)
            ctx.stroke()
        else:
            # Draw container border (thinner)
            ctx.set_source_rgba(0.4, 0.4, 0.4, 0.2)
            ctx.rectangle(r.x, r.y, r.width, r.height)
            ctx.stroke()
            
            # Layout Indicator
            if node.layout in ['tabbed', 'stacked']:
                ctx.save()
                ctx.set_source_rgb(1.0, 1.0, 1.0)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                # Scale font size inversely to current scale to keep text readable constant size? 
                # No, just pick a reasonable size relative to coordinates.
                # Since we scaled the context, 20 units might be huge or tiny depending on screen res.
                # Assuming 1080p workspace, 20px is small.
                ctx.set_font_size(30)
                ctx.move_to(r.x + 10, r.y + 40)
                label = "T" if node.layout == 'tabbed' else "S"
                ctx.show_text(label)
                ctx.restore()

        # Recurse
        for child in node.nodes:
            self.draw_node(ctx, child)
        
        # Floating nodes (drawn on top)
        for child in node.floating_nodes:
            self.draw_node(ctx, child)

