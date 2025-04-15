import time
import psutil
from rich.live import Live
from utils import *
from interface import generate_output_renderable, console

def main():
    # Initialize state variables here
    last_net_io = psutil.net_io_counters()
    last_time = time.time()

    # Initial renderable generation
    initial_renderable, last_net_io, last_time = generate_output_renderable(last_net_io, last_time)

    with Live(initial_renderable, refresh_per_second=1, screen=True, vertical_overflow="visible") as live:
        while True:
            try:
                # Generate renderable and update state
                new_renderable, last_net_io, last_time = generate_output_renderable(last_net_io, last_time)
                live.update(new_renderable)
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print_exception(show_locals=True)
                break

if __name__ == "__main__":
    main()
