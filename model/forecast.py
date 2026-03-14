from matplotlib import pyplot as plt

from core_model import (fit_iterated_intraday_arma,
                        forecast_next_day_mean,
                        get_season_dummy,
                        fit_garch_panel,
                        forecast_garch_sigma,
                        fit_lightgbm_intraday_mean,
                        forecast_next_day_mean_ml)

from acdamic_graph import (plot_intraday_forecast,
                           plot_average_intraday_profile,
                           plot_rmse_by_interval,
                           plot_intraday_fan_chart)

from data_preparation import prepare_generation_panel

import numpy as np
import pandas as pd

FUELTECH = "solar"
MEAN_MODEL = ("lightgbm", "arma")

def run_rolling_intraday_forecast(
    df: pd.DataFrame,
    init_window: int,
    mean_model: str = MEAN_MODEL[1]
) -> pd.DataFrame | None:
    """
    Expanding-window rolling forecast returning
    tidy pandas DataFrame.
    """

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "interval"])

    unique_dates = df["date"].drop_duplicates().sort_values()

    records = []

    # ---------------------------------------
    # seasonal helper
    # ---------------------------------------
    def get_season_dummy(date):

        m = date.month
        return np.array([
            int(m in [12,1,2]),
            int(m in [3,4,5]),
            int(m in [9,10,11]),
        ])

    # ---------------------------------------
    # rolling forecast loop
    # ---------------------------------------
    for t in range(init_window, len(unique_dates)-1):

        # train_dates = unique_dates[:t]
        train_dates = unique_dates[max(0, t - init_window):t]
        forecast_date = unique_dates.iloc[t]
        season_next_day = get_season_dummy(forecast_date)

        train_df = df[df.date.isin(train_dates)]

        # ===============================
        # PANEL BUILD
        # ===============================
        y_train = (
            train_df
            .pivot(index="date",
                   columns="interval",
                   values="generation")
            .sort_index()
        )

        season_train = (
            train_df[["date","D_SU","D_AU","D_SP"]]
            .drop_duplicates("date")
            .set_index("date")
            .sort_index()
            .values
        )

        # ===============================
        # FIT ARMA MODEL
        # ===============================
        if mean_model == "arma":
            fit = fit_iterated_intraday_arma(
                y_panel=y_train.values,
                season=season_train
            )
            pass
            forecast = forecast_next_day_mean(
                y_last_day=y_train.values[-1],
                season_next_day=season_next_day,
                residuals_last_day=fit.residuals[-1],
                residuals_prev_day=fit.residuals[-2],
                betas=fit.betas,
            )
        elif mean_model == "lightgbm":

            # ===============================
            # FIT ML/LightGBM MODEL
            # ==============================

            fit = fit_lightgbm_intraday_mean(y_panel=y_train.values,
                                             season=season_train)

            forecast = forecast_next_day_mean_ml(
                y_last_day=y_train.values[-1],
                season_next_day=season_next_day,
                residuals_last_day=fit.residuals[-1],
                residuals_prev_day=fit.residuals[-2],
                models=fit.models
            )

        else:

            print("Unknown model")
            return None

        # ===============================
        # FIT GARCH MODEL
        # ===============================
        #TODO: Fit garch model on the residual

        garch_models = fit_garch_panel(
            fit.residuals
        )
        sigma_forecast = forecast_garch_sigma(
            garch_models
        )


        # ===============================
        # FORECAST
        # ===============================


        # ===============================
        # ACTUAL DATA
        # ===============================
        actual = (
            df[df.date == forecast_date]
            .pivot(index="date",
                   columns="interval",
                   values="generation")
            .values[0]
        )

        intervals = y_train.columns

        # ===============================
        # STORE TIDY ROWS
        # ===============================
        for i, interval in enumerate(intervals):

            records.append({
                "date": forecast_date,
                "interval": interval,
                "forecast": forecast[i],
                "sigma": sigma_forecast[i],
                "actual": actual[i],
                "model": mean_model
            })

    results_df = pd.DataFrame(records)

    return results_df



df = pd.read_csv("wind_solar_qld_sa_adam_clement_data.csv")

data = prepare_generation_panel(df=df, fueltech= FUELTECH)
forecasts = run_rolling_intraday_forecast(
    df=data,
    init_window=500
)
pass
# forecasts = pd.read_csv("adam_clement_data_forecast_results_wind.csv")

plot_intraday_fan_chart(df=forecasts,
                        start_date="2021-04-18",
                        end_date="2021-04-20",
                        fueltech = FUELTECH)

plot_intraday_forecast(
    results_df=forecasts,
    date="2021-04-14",
    fueltech = FUELTECH
)
pass
plot_average_intraday_profile(
    results_df=forecasts,
    fueltech = FUELTECH)

rmse_table = plot_rmse_by_interval(results_df=forecasts, fueltech = FUELTECH)