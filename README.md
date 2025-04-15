# live-monitor

A simple live terminal monitor for system stats using `psutil` and `rich`.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <https://github.com/Squeeshalami/live-monitor.git>
    cd live-monitor
    ```
2.  **Install dependencies using uv:**
    ```bash
    uv sync
    ```

## Usage

Run the monitor from the project directory:

```bash
uv run main.py
```

Or, if you have set up the `livemonitor` command:

```bash
livemonitor
```

Press `Ctrl+C` to exit.
