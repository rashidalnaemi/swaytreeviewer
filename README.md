# Sway Tree Visualizer

A Python application that visualizes the Sway window manager layout tree in real-time. It uses GTK3 for the interface and `i3ipc` to communicate with Sway.

## Requirements

*   Python 3
*   GTK 3 (usually installed by default on most Linux distributions)
*   Sway Window Manager

## Installation

1.  Clone the repository:
    ```python
    git clone https://github.com/yourusername/swaytreeviewer.git
    cd swaytreeviewer
    ```

You might face some dependency errors which require you to run `pip install -r requirements.txt` but that is unlikely as the only two dependencies are i3ipc and PyGObject which are installed by default when using SwayWM.


## Usage

You can start the application by running main.py

```
python3 main.py
```

## Command Line Options

The application supports different display modes to suit your workflow.

### `--mode`

Controls how the application window is displayed.

*   **Syntax:** `python3 --mode <MODE>`
*   **Default:** `window`

**Available Modes:**

*   `window`: Standard GTK window. Managed like any other tiled window in Sway.
*   `transparent`: Opens as a floating, semi-transparent window. Good for overlay usage.

**Examples:**

Run in floating mode:
```python
python3 main.py --mode floating
```

Run as a transparent overlay:
```python
python3 main.py --mode transparent
```

### `--include-floating`

Controls whether floating windows are included in the visualization. By default, they are ignored to focus on the tiling layout.

*   **Syntax:** `python3 main.py --include-floating`
*   **Default:** Disabled (Floating windows are ignored)

**Example:**

```python
python3 main.py --include-floating
```

### `--alpha`

Sets the opacity of the visualization elements (backgrounds, borders, text). This is particularly effective when combined with `transparent` mode.

*   **Syntax:** `python3 main.py --alpha <VALUE>`
*   **Value:** A float between `0.0` (fully transparent) and `1.0` (fully opaque).
*   **Default:** `1.0`

**Example:**

Run with 50% opacity:
```python
python3 main.py --mode transparent --alpha 0.5
```

### `--width` and `--height`

Sets the initial dimensions of the window. You can specify the size in **pixels** or as a **percentage** of the screen size.

*   **Syntax:** `python3 main.py --width <VALUE> --height <VALUE>`
*   **Value:** An integer (pixels) or a string ending in `%` (percentage).
*   **Defaults:**
    *   Width: `500` (pixels)
    *   Height: `400` (pixels)

**Examples:**

Set specific pixel dimensions:
```python
python3 main.py --width 800 --height 600
```

Set dimensions relative to screen size:
```python
python3 main.py --width 50% --height 50%
```

Mix pixels and percentages:
```python
python3 main.py --width 100% --height 300
```

## Troubleshooting

If the window does not float automatically in `transparent` modes, ensure that your Sway configuration allows the application to control its own window state, or manually toggle floating mode using your Sway keybindings.
