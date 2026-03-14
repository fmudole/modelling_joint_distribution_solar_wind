import matplotlib.pyplot as plt
import pandas as pd


def plot_intraday_forecast(
    results_df: pd.DataFrame,
    date,
    fueltech: str = "wind",
    interval_minutes: int = 30,
    save_path: str | None = None,
):
    """
    Plot forecast vs actual for one day
    in academic paper style.
    """

    # -----------------------------------
    # Select single day
    # -----------------------------------
    day_df = results_df[
        results_df["date"] == pd.to_datetime(date)
    ].sort_values("interval")

    if day_df.empty:
        raise ValueError("Date not found in results")

    # -----------------------------------
    # Create intraday time axis
    # -----------------------------------
    time_axis = (
        pd.to_datetime(day_df["date"])
        + pd.to_timedelta(
            (day_df["interval"] - 1) * interval_minutes,
            unit="min"
        )
    )

    # -----------------------------------
    # Academic styling
    # -----------------------------------
    plt.figure(figsize=(10,5))

    plt.plot(
        time_axis,
        day_df["actual"],
        label="Actual",
        linewidth=2,
        color="black"
    )

    plt.plot(
        time_axis,
        day_df["forecast"],
        label="Forecast",
        linewidth=2,
        linestyle="--",
        color="royalblue"
    )

    # -----------------------------------
    # Labels
    # -----------------------------------
    plt.xlabel("Time")
    plt.ylabel("Generation (MW)")
    plt.title(f"Intraday Forecast vs Actual — {date}")

    plt.legend(frameon=False)

    plt.grid(
        True,
        linestyle=":",
        linewidth=0.7,
        alpha=0.7
    )

    plt.tight_layout()

    # -----------------------------------
    # Save (paper ready)
    # -----------------------------------
    if save_path:
        plt.savefig(save_path, dpi=300)

    plt.show()

def plot_average_intraday_profile(
    results_df: pd.DataFrame,
    save_path: str | None = None,
):
    """
    Academic-style average intraday profile plot.
    """

    # -----------------------------------
    # Average across days
    # -----------------------------------
    avg_profile = (
        results_df
        .groupby("interval")[["forecast", "actual"]]
        .mean()
        .reset_index()
        .sort_values("interval")
    )

    # -----------------------------------
    # Plot
    # -----------------------------------
    plt.figure(figsize=(10,5))

    plt.plot(
        avg_profile["interval"],
        avg_profile["actual"],
        color="black",
        linewidth=2,
        label="Average Actual"
    )

    plt.plot(
        avg_profile["interval"],
        avg_profile["forecast"],
        linestyle="--",
        color="royalblue",
        linewidth=2,
        label="Average Forecast"
    )

    # -----------------------------------
    # Labels
    # -----------------------------------
    plt.xlabel("Intraday Interval")
    plt.ylabel("Generation (MW)")
    plt.title("Average Intraday Generation Profile")

    plt.legend(frameon=False)

    plt.grid(
        linestyle=":",
        linewidth=0.7,
        alpha=0.7
    )

    plt.tight_layout()

    # -----------------------------------
    # Save for paper
    # -----------------------------------
    if save_path:
        plt.savefig(save_path, dpi=300)

    plt.show()

import numpy as np
import matplotlib.pyplot as plt


def plot_rmse_by_interval(
    results_df,
    save_path: str | None = None,
    fueltech: str = "wind"
):
    """
    Academic-style RMSE by intraday interval.
    """

    # -----------------------------------
    # RMSE computation
    # -----------------------------------
    rmse_interval = (
        results_df
        .assign(
            sq_error=lambda x:
            (x["forecast"] - x["actual"])**2
        )
        .groupby("interval")["sq_error"]
        .mean()
        .pipe(np.sqrt)
        .reset_index(name="RMSE")
    )

    # -----------------------------------
    # Plot
    # -----------------------------------
    plt.figure(figsize=(10,5))

    plt.plot(
        rmse_interval["interval"],
        rmse_interval["RMSE"],
        color="black",
        linewidth=2
    )

    plt.xlabel("Intraday Interval")
    plt.ylabel("RMSE (MW)")
    plt.title(f"Forecast {fueltech} RMSE by Intraday Interval")

    plt.grid(
        linestyle=":",
        linewidth=0.7,
        alpha=0.7
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)

    plt.show()

    return rmse_interval

def plot_intraday_fan_chart(
    df: pd.DataFrame,
    start_date=None,
    end_date=None,
    intervals_per_day=48,
    fueltech = "wind"
):
    """
    Plot probabilistic fan chart using
    forecast mean + GARCH sigma.

    Required columns:
        date | interval | forecast | sigma | actual
    """
    pass
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])

    # ---------------------------
    # filter dates
    # ---------------------------
    if start_date is not None:
        data = data[data.date >= pd.to_datetime(start_date)]

    if end_date is not None:
        data = data[data.date <= pd.to_datetime(end_date)]

    # continuous time index
    data = data.sort_values(["date", "interval"])
    data["t"] = np.arange(len(data))

    mu = data["forecast"].values
    sigma = data["sigma"].values

    # ---------------------------
    # probability bands
    # ---------------------------
    bands = [
        (0.52, 0.48),
        (0.84, 0.16),
        (1.28, 0.10),
        (1.64, 0.05),
    ]

    plt.figure(figsize=(15,7))

    # draw widest band first
    for k, alpha in reversed(bands):

        upper = mu + k * sigma
        lower = mu - k * sigma

        plt.fill_between(
            data["t"],
            lower,
            upper,
            alpha=alpha,
            linewidth=0
        )

    # ---------------------------
    # mean forecast
    # ---------------------------
    plt.plot(
        data["t"],
        mu,
        linestyle="--",
        label=f"Forecast Mean-{fueltech}"
    )

    # ---------------------------
    # actual
    # ---------------------------
    plt.plot(
        data["t"],
        data["actual"],
        color="black",
        linewidth=1.5,
        label=f"Actual-{fueltech}"
    )

    # vertical daily separators
    for i in range(0, len(data), intervals_per_day):
        plt.axvline(i, linewidth=0.5)

    plt.title(f"Intraday Probabilistic Fan Chart of {fueltech}")
    plt.xlabel("Time")
    plt.ylabel("Generation (MW)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()