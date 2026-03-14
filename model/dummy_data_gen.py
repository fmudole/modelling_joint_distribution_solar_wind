"""
Disclaimer:
The dataset used in this study for demonstration and development purposes was synthetically generated using assistance from ChatGPT (OpenAI).
The data are entirely artificial and do not represent real-world electricity generation or market outcomes.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from core_model import fit_iterated_intraday_arma, forecast_next_day_mean, get_season_dummy

np.random.seed(42)

def generate_dummy_intraday_data(
    n_days: int = 700,
    n_intervals: int = 48
):

    dates = pd.date_range("2020-01-01", periods=n_days, freq="D")

    records = []

    # --- seasonal baseline ---
    def seasonal_level(month):
        if month in [12, 1, 2]:   # summer
            return 0.7
        elif month in [3, 4, 5]:  # autumn
            return 0.5
        elif month in [9, 10, 11]:  # spring
            return 0.6
        else:
            return 0.4  # winter baseline

    # store yesterday values
    prev_day = np.zeros(n_intervals)

    for d, date in enumerate(dates):

        month = date.month
        season_base = seasonal_level(month)

        # season dummies
        D_SU = int(month in [12, 1, 2])
        D_AU = int(month in [3, 4, 5])
        D_SP = int(month in [9, 10, 11])

        today = np.zeros(n_intervals)

        for i in range(n_intervals):

            # intraday smooth shape (solar/wind pattern)
            intraday_pattern = np.sin(
                2 * np.pi * i / n_intervals
            )

            # daily persistence
            daily_component = 0.6 * prev_day[i]

            # intraday persistence
            intra_component = (
                0.3 * today[i - 1] if i > 0 else 0
            )

            # stochastic shock
            noise = np.random.normal(0, 0.15)

            value = (
                season_base
                + 0.5 * intraday_pattern
                + daily_component
                + intra_component
                + noise
            )

            value = max(value, 0)  # generation can't be negative
            today[i] = value

            records.append(
                {
                    "date": date,
                    "interval": i + 1,
                    "generation": value,
                    "D_SU": D_SU,
                    "D_AU": D_AU,
                    "D_SP": D_SP,
                }
            )

        prev_day = today.copy()

    return pd.DataFrame(records)



df = generate_dummy_intraday_data()

