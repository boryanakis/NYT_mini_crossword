#!/usr/bin/env python
"""
Generates a plot of crossword statistics generated by the crossword crate

It expects two positional arguments:
1. The path to a CSV file generated from the crossword crate
2. The output path and filename where the rendered plot should be saved. Both SVG and PNG formats
are supported.
"""

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import sys


def parse_data(csv_path):
    """Parse crossword database stored at the given path into a pandas DataFrame. The DataFrame
    only contains solve data for unaided, solved puzzles and is sorted by the index, the time when
    each puzzle was solved.

    Interesting columns in the returned DataFrame:
    solve_time_secs
    weekday
    """
    df = pd.read_csv(csv_path, parse_dates=["date"], index_col="date")
    df["Solved datetime"] = pd.to_datetime(df["solved_unix"], unit="s")
    # Use the date solved rather than the puzzle date as the index.
    # Puzzle date is interesting for analyzing puzzle difficulty over time (but skewed by change
    # in ability over time)
    # Date solved is interesting for analyzing change in solving ability over time (assuming puzzle
    # difficulty is a constant)
    df.index = df["Solved datetime"]
    df = df.sort_index()
    # Filter out:
    # * Puzzles that were solved more than 7 days after first open. These puzzles were revisited
    # much later, making it hard to make accurate conclusions about the solve time.
    # * Unsolved puzzles
    # * Puzzles where cheats were used
    df = df[
        (df["solved_unix"] - df["opened_unix"] < 3600 * 24 * 7)
        & (df["cheated"] == False)
        & df.solve_time_secs.notnull()
    ]

    return df


def save_plot(df, out_path):
    DAYS = df["weekday"].unique()

    # Pick an appropriate y-axis, balancing being robust to outliers vs. showing all data
    Y_MAX = df["solve_time_secs"].quantile(0.99) / 60

    fig = plt.figure(figsize=(10, 7), dpi=200)
    plt.title("NYT crossword solve time (8-week rolling average) by date of solve")
    ax = fig.gca()
    for day in DAYS:
        rolling_avg = df[df["weekday"] == day]["solve_time_secs"].rolling("56D").mean()
        (rolling_avg / 60.0).plot(
            ax=ax, label=day, linewidth=2, markersize=20, marker=",", linestyle="-"
        )
    plt.legend()

    ax.set_xlabel("Date solved")
    ax.set_ylabel("Minutes")
    minor_yticks = np.arange(0, Y_MAX + 1, 5)
    ax.set_ylim(0, Y_MAX)
    ax.set_yticks(minor_yticks, minor=True)

    plt.grid(True, which="both", axis="both")
    plt.savefig(out_path)


def main():
    sns.set_style("ticks")

    try:
        in_file = sys.argv[1]
        out_file = sys.argv[2]
    except:
        print(
            "Required arguments not given. Usage: {} <input_csv_file> <output_file>".format(
                sys.argv[0]
            )
        )
        return

    df = parse_data(in_file)
    save_plot(df, out_file)


if __name__ == "__main__":
    main()