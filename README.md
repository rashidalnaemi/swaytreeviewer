# Sway Tree Visualizer

A Python application that visualizes the Sway window manager layout tree in real-time. It uses GTK3 for the interface and `i3ipc` to communicate with Sway.

## Requirements

*   Python 3
*   GTK 3 (usually installed by default on most Linux distributions)
*   Sway Window Manager

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/swaytreeviewer.git
    cd swaytreeviewer
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

You can start the application using the provided `run.sh` script:

```bash
./run.sh
```

Alternatively, if you prefer to run it manually with Python, make sure to set the `PYTHONPATH`:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 src/main.py
```

## Command Line Options

The application supports different display modes to suit your workflow.

### `--mode`

Controls how the application window is displayed.

*   **Syntax:** `./run.sh --mode <MODE>`
*   **Default:** `window`

**Available Modes:**

*   `window`: Standard GTK window. Managed like any other tiled window in Sway.
*   `floating`: Opens as a floating window. Useful if you want to keep it above other tiled windows.
*   `transparent`: Opens as a floating, semi-transparent window. Good for overlay usage.
*   `fullscreen-transparent`: Opens as a fullscreen, semi-transparent overlay.

**Examples:**

Run in floating mode:
```bash
./run.sh --mode floating
```

Run as a transparent overlay:
```bash
./run.sh --mode transparent
```

## Troubleshooting

If the window does not float automatically in `floating` or `transparent` modes, ensure that your Sway configuration allows the application to control its own window state, or manually toggle floating mode using your Sway keybindings.
