
import matplotlib
# Don't force Qt5Agg if you're still getting the Qt "xcb" error.
# Use a working GUI backend on your system.

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pathlib import Path
import ast
import re

MAX_TIME = 10 * 60  # 10 minutes in seconds
LOG_FILE = Path("runs/1.txt")

fig, axes = plt.subplots(2, 2, figsize=(13, 8))
fig.suptitle("Robot Flocking Metrics", fontsize=16)


def read_log():
    records = []

    if not LOG_FILE.exists():
        print("Log file not found:", LOG_FILE.resolve())
        return records

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                # Split only at the first two commas.
                frame, time_value, metrics_text = line.strip().split(",", 2)

                # Convert NumPy representations to ordinary numbers.
                metrics_text = re.sub(
                    r"np\.(?:int64|int32|float64|float32)\(([-+0-9.eE]+)\)",
                    r"\1",
                    metrics_text
                )

                metrics = ast.literal_eval(metrics_text)

                time_seconds = float(time_value)

                if time_seconds <= MAX_TIME:
                    records.append({
                        "frame": int(frame),
                        "time": time_seconds,
                        "metrics": metrics
                    })

            except (ValueError, SyntaxError) as error:
                print("Could not read log line:", line.strip())
                print("Reason:", error)

    return records


def update(frame):
    records = read_log()

    if not records:
        return

    times = [r["time"] for r in records]
    metrics = [r["metrics"] for r in records]

    flock_counts = [m["number_of_flocks"] for m in metrics]
    largest_flocks = [m["largest_flock"] for m in metrics]
    isolated = [m["isolated_robots"] for m in metrics]
    percentages = [m["flock_percentage"] for m in metrics]

    for ax in axes.flat:
        ax.clear()

    for ax in axes.flat:
     ax.set_xlim(0, MAX_TIME)

    axes[0, 0].plot(times, flock_counts)
    axes[0, 0].set_title("Number of Flocks")
    axes[0, 0].set_xlabel("Time (s)")
    axes[0, 0].set_ylabel("Flocks")
    axes[0, 0].grid()

    axes[0, 1].plot(times, largest_flocks)
    axes[0, 1].set_title("Largest Flock")
    axes[0, 1].set_xlabel("Time (s)")
    axes[0, 1].set_ylabel("Robots")
    axes[0, 1].grid()

    axes[1, 0].plot(times, isolated)
    axes[1, 0].set_title("Isolated Robots")
    axes[1, 0].set_xlabel("Time (s)")
    axes[1, 0].set_ylabel("Robots")
    axes[1, 0].grid()

    axes[1, 1].plot(times, percentages)
    axes[1, 1].set_title("Percentage of Robots in Flocks")
    axes[1, 1].set_xlabel("Time (s)")
    axes[1, 1].set_ylabel("Percentage (%)")
    axes[1, 1].set_ylim(0, 100)
    axes[1, 1].grid()

    plt.tight_layout()


ani = animation.FuncAnimation(
    fig,
    update,
    interval=1000,
    cache_frame_data=False
)

plt.show()
