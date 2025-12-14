import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

# Layout Constants
PAD = 5
HEADER_H = 20

class TreeVisualizer(Gtk.Window):
    def __init__(self, mode="window", include_floating=False, alpha=0.5, width="100%", height="100%"):
        super().__init__(title="SwayTreeViewer")
        self.set_wmclass("swaytreeviewer", "SwayTreeViewer")
        self.mode = mode
        self.include_floating = include_floating
        self.alpha = alpha
        
        # Calculate actual dimensions
        final_w, final_h = self._calculate_dimensions(width, height)
        self.set_default_size(final_w, final_h)
        self.set_keep_above(True) # Keep window on top
        
        # Mode Configuration
        if self.mode == "transparent":
            # Enable transparency
            screen = self.get_screen()
            visual = screen.get_rgba_visual()
            if visual and screen.is_composited():
                self.set_visual(visual)
                self.set_app_paintable(True)

        if self.mode == "transparent":
            # Remove decorations (title bar, borders)
            self.set_decorated(False)

        # Make the window floating and sticky via hints (for utility windows)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        
        # Prevent window from stealing focus on start
        self.set_focus_on_map(False)
        
        # Handle key press events
        self.connect("key-press-event", self.on_key_press)
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.add(self.drawing_area)
        
        self.current_tree = None
        self.focused_workspace_name = None

    def _calculate_dimensions(self, w_str, h_str):
        """Parse width/height strings (pixels or percentage) and return pixels."""
        screen = self.get_screen()
        monitor_w = screen.get_width()
        monitor_h = screen.get_height()

        def parse_dim(dim_str, max_dim):
            try:
                dim_str = str(dim_str).strip()
                if dim_str.endswith("%"):
                    pct = float(dim_str[:-1])
                    return int(max_dim * (pct / 100.0))
                else:
                    return int(dim_str)
            except ValueError:
                return 500 if max_dim == monitor_w else 400

        return parse_dim(w_str, monitor_w), parse_dim(h_str, monitor_h)

    def update_tree(self, tree, focused_ws_name):
        self.current_tree = tree
        self.focused_workspace_name = focused_ws_name
        self.queue_draw()

    def find_node_by_name(self, node, name):
        if node.name == name and node.type == 'workspace':
            return node
        
        children = node.nodes
        if self.include_floating:
            children = children + node.floating_nodes

        for child in children:
            res = self.find_node_by_name(child, name)
            if res: return res
        return None

    def get_node_path(self, root, target_id):
        if root.id == target_id:
            return [root]
        
        children = root.nodes
        if self.include_floating:
            children = children + root.floating_nodes

        for child in children:
            path = self.get_node_path(child, target_id)
            if path:
                return [root] + path
        return None

    def on_key_press(self, widget, event):
        """Handle key press events."""
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def on_draw(self, widget, ctx):
        # 1. Clear/Draw Window Background
        if self.mode == "transparent":
            # Clear background fully for transparency
            ctx.set_source_rgba(0, 0, 0, 0)
            ctx.set_operator(cairo.OPERATOR_SOURCE)
            ctx.paint()
            ctx.set_operator(cairo.OPERATOR_OVER)
        else:
            # Standard dark background
            ctx.set_source_rgb(0.15, 0.15, 0.15)
            ctx.paint()

        if not self.current_tree or not self.focused_workspace_name:
            return

        ws_node = self.find_node_by_name(self.current_tree, self.focused_workspace_name)

        if ws_node:
            w_width = widget.get_allocated_width()
            w_height = widget.get_allocated_height()
            
            avail_y = 5 # Default small padding
            
            # Header Breadcrumbs (Only in Window mode)
            if self.mode == "window":
                path = self.get_node_path(self.current_tree, ws_node.id)
                path_str = " > ".join([n.name or n.type for n in path]) if path else "Root"
                
                ctx.save()
                ctx.set_source_rgb(0.8, 0.8, 0.8)
                ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(12)
                ctx.move_to(10, 20)
                ctx.show_text(path_str)
                ctx.restore()
                
                avail_y = 30
            
            # Available area for the tree
            avail_h = w_height - avail_y - 10
            avail_w = w_width - 20
            
            # Aspect Ratio Correction
            # Get actual workspace geometry
            ws_rect = ws_node.rect
            if ws_rect.width and ws_rect.height:
                ws_ratio = ws_rect.width / ws_rect.height
                win_ratio = avail_w / avail_h
                
                final_w = avail_w
                final_h = avail_h
                
                if ws_ratio > win_ratio:
                    # Workspace is wider than window: constrain by width
                    final_h = avail_w / ws_ratio
                else:
                    # Workspace is taller than window: constrain by height
                    final_w = avail_h * ws_ratio
                
                # Center it
                offset_x = 10 + (avail_w - final_w) / 2
                offset_y = avail_y + (avail_h - final_h) / 2
                
                self.draw_node_recursive(ctx, ws_node, offset_x, offset_y, final_w, final_h)
            else:
                # Fallback if no geometry info
                self.draw_node_recursive(ctx, ws_node, 10, avail_y, avail_w, avail_h)

    def draw_node_recursive(self, ctx, node, x, y, w, h):
        if w <= 0 or h <= 0: return

        is_leaf = len(node.nodes) == 0
        
        # Colors (Polished)
        border_color = (0.3, 0.3, 0.3)
        border_width = 1
        # Apply alpha to background colors
        bg_color = (0.1, 0.1, 0.1, 1.0 * self.alpha) # Dark background for containers

        if node.focused:
            border_color = (0.3, 0.7, 1.0) # Soft Blue
            border_width = 2
            bg_color = (0.1, 0.2, 0.3, 1.0 * self.alpha) # Dark Blue tint
        elif is_leaf:
            bg_color = (0.18, 0.18, 0.18, 1.0 * self.alpha) # Slightly lighter for windows

        # 1. Draw Background (Bottom Layer)
        ctx.save()
        ctx.rectangle(x, y, w, h)
        ctx.set_source_rgba(*bg_color)
        ctx.fill() # Only fill
        ctx.restore()

        # Determine Label
        label = ""
        if node.type == 'workspace':
            label = f"WS: {node.name}"
        elif node.type == 'con':
            if is_leaf:
                label = node.name if node.name else "unnamed"
            else:
                label = f"{node.layout}"
        elif node.type == 'floating_con':
            label = "Float"
        
        # 2. Draw Header Label (Middle Layer A)
        # Use a dynamic header height based on size, but clamped
        
        # FIX: If the node is very small (likely a tab or collapsed stack item),
        # force the header to fill the space so text is visible.
        if h < HEADER_H * 1.5:
             header_h = h - 2 # Use almost full height
        else:
             header_h = min(HEADER_H, h * 0.3) 
        
        if header_h > 8: # Only draw header if space permits
            ctx.save()
            ctx.rectangle(x, y, w, header_h)
            ctx.clip()
            
            # Text Color
            text_color = (0.7, 0.7, 0.7)
            if node.focused: text_color = (1.0, 1.0, 1.0)
            
            # Center vertically in the header strip
            ctx.move_to(x + 4, y + (header_h / 2) + 4) 
            
            ctx.set_source_rgba(*text_color, self.alpha)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(min(10, header_h - 2))
            ctx.show_text(label)
            ctx.restore()

        # Calculate Content Area for Children
        # If header was too small, don't reserve space for it
        effective_header_h = header_h if header_h > 8 else 0
        
        # If this is a "Collapsed" view (header takes up most space), don't draw content
        if h < HEADER_H * 1.5:
            effective_header_h = h # Consume all space
        
        cx = x + PAD
        cy = y + effective_header_h
        cw = w - (2 * PAD)
        ch = h - effective_header_h - PAD

        if cw > 0 and ch > 0:
            # 3. Recurse for Children (Middle Layer B)
            if not is_leaf:
                children = node.nodes
                count = len(children)
                if count > 0:
                    # Layout Logic
                    if node.layout in ['splith', 'splitv']:
                        # Calculate total size in Sway units to determine ratios
                        # Note: node.rect might not exactly match sum of children due to borders/gaps in sway
                        # So we sum children.
                        total_sway_size = 0
                        if node.layout == 'splith':
                            total_sway_size = sum(c.rect.width for c in children)
                        else:
                            total_sway_size = sum(c.rect.height for c in children)
                        
                        if total_sway_size == 0: total_sway_size = 1 # avoid div/0

                        curr_pos = 0
                        for child in children:
                            ratio = 0
                            if node.layout == 'splith':
                                ratio = child.rect.width / total_sway_size
                                child_w = cw * ratio
                                self.draw_node_recursive(ctx, child, cx + curr_pos, cy, child_w, ch)
                                curr_pos += child_w
                            else: # splitv
                                ratio = child.rect.height / total_sway_size
                                child_h = ch * ratio
                                self.draw_node_recursive(ctx, child, cx, cy + curr_pos, cw, child_h)
                                curr_pos += child_h

                    elif node.layout in ['tabbed', 'stacked']:
                        # Identify Active Child
                        active_child = None
                        if node.focus:
                            active_id = node.focus[0]
                            active_child = next((c for c in children if c.id == active_id), children[0])
                        else:
                            active_child = children[0]

                        TAB_SIZE = 22 # Height of headers
                        
                        if node.layout == 'tabbed':
                            # TABBED: Top Horizontal Strip for Headers + Main Area for Active Content
                            tab_w = cw / count
                            
                            # 1. Draw All Tabs (Inactive headers)
                            # We draw the active tab here too as a marker?
                            # Yes, draw all as headers in the strip.
                            for i, child in enumerate(children):
                                tx = cx + (i * tab_w)
                                ty = cy
                                tw = tab_w
                                th = TAB_SIZE
                                
                                if child == active_child:
                                    # Highlight Active Tab
                                    ctx.save()
                                    ctx.rectangle(tx, ty, tw, th)
                                    ctx.set_source_rgba(0.2, 0.6, 1.0, self.alpha) # Blue
                                    ctx.fill()
                                    # Add label explicitly? No, draw_node_recursive below will handle frame/label if we call it.
                                    # But we want to draw the BODY primarily.
                                    # Let's draw a "Tab Marker" here.
                                    ctx.restore()
                                else:
                                    # Draw Inactive Tab (Recurse -> renders frame/header)
                                    self.draw_node_recursive(ctx, child, tx, ty, tw, th)

                            # 2. Draw Active Body
                            body_y = cy + TAB_SIZE
                            body_h = ch - TAB_SIZE
                            if body_h > 0:
                                self.draw_node_recursive(ctx, active_child, cx, body_y, cw, body_h)

                        else: 
                            # STACKED: Accordion (Vertical List)
                            # Inactive get Header height. Active gets remaining.
                            
                            inactive_count = count - 1
                            req_header_space = inactive_count * TAB_SIZE
                            
                            # Header height for inactive nodes
                            h_h = TAB_SIZE
                            if req_header_space > ch * 0.6: # If headers take > 60% of space, compress
                                h_h = (ch * 0.6) / inactive_count if inactive_count > 0 else TAB_SIZE

                            curr_y = cy
                            for child in children:
                                if child == active_child:
                                    # Active gets remaining space
                                    rem_h = ch - (inactive_count * h_h)
                                    self.draw_node_recursive(ctx, child, cx, curr_y, cw, rem_h)
                                    curr_y += rem_h
                                else:
                                    # Inactive gets header space
                                    self.draw_node_recursive(ctx, child, cx, curr_y, cw, h_h)
                                    curr_y += h_h

            if self.include_floating:
                for child in node.floating_nodes:
                    fw = w * 0.5
                    fh = h * 0.5
                    fx = x + (w - fw) / 2
                    fy = y + (h - fh) / 2
                    self.draw_node_recursive(ctx, child, fx, fy, fw, fh)

        # 4. Draw Border (Top Layer - Ensures Focus is Visible)
        ctx.save()
        ctx.rectangle(x, y, w, h)
        ctx.set_source_rgba(*border_color, self.alpha)
        ctx.set_line_width(border_width)
        ctx.stroke()
        ctx.restore()
