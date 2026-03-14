"""
Author: Franklin Mudole
Disclamair
This work is taken from replication of Adam Clement matlab code and the use of chatGPT was utilise in helping understand
matlab code.
"""
from statistics import LinearRegression

import numpy as np
import pandas as pd
from dataclasses import dataclass
from scipy.optimize import minimize
from scipy.stats import t as student_t
import statsmodels.api as sm
from arch import arch_model

import lightgbm as lgb

## -------------------------------------------- helper function -------------------------------------------------------
def get_season_dummy(date):

    m = date.month

    D_SU = int(m in [12,1,2])
    D_AU = int(m in [3,4,5])
    D_SP = int(m in [9,10,11])

    return np.array([D_SU, D_AU, D_SP])

def fit_ols(y: np.ndarray, X: np.ndarray):
    """
    Fits OLS with intercept.
    Returns fitted OLS model, and fitted values
    :param y:
    :param X:
    :return:
    """
    Xc = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y, Xc).fit()
    return model.params, model.fittedvalues

"""
def build_mean_features(y_panel: np.ndarray,
                        season: np.ndarray,
                        residuals: np.ndarray,
                        interval_idx: int):
    T, I = y_panel.shape
    i = interval_idx
    y = y_panel[:, i]

    # daily AR(1): y[t-1, i]
    daily_ar = np.roll(y_panel[:, i], 1)
    daily_ar[0] = np.nan

    #intraday AR(1): y[t, i-1]
    if i == 0:
        intra_ar = np.zeros(T)
    else:
        intra_ar = y_panel[:, i-1]

    # daily MA(1): eps[t-1, i]
    daily_ma = np.roll(residuals[:, i], 1)
    daily_ma[0] = np.nan

    # intraday MA(1): eps[t, i-1]
    if i == 0:
        intra_ma = intra_ma = np.zeros(T)
    else:
        intra_ma = residuals[:, i-1]

    X = np.column_stack([daily_ar, intra_ar, season ,daily_ma, intra_ma]) ## X matrix in yt = X * beta_t
    mask = np.isfinite(y) & np.all(np.isfinite(X), axis=1) ## checks whether the numbers are valid.

    return y[mask], X[mask], mask

"""

def build_mean_features(y_panel: np.ndarray,
                        season: np.ndarray,
                        residuals: np.ndarray,
                        interval_idx: int):

    T, I = y_panel.shape
    i = interval_idx
    y = y_panel[:, i]

    # ----------------------------
    # DAILY AR(1): y[t-1, i]
    # ----------------------------
    daily_ar = np.roll(y_panel[:, i], 1)
    daily_ar[0] = np.nan

    # ----------------------------
    # INTRADAY AR(1): y[t, i-1]
    # ----------------------------
    if i == 0:
        intra_ar = np.zeros(T)
    else:
        intra_ar = y_panel[:, i-1]

    # ----------------------------
    # DAILY MA(1): eps[t-1, i]
    # ----------------------------
    daily_ma = np.roll(residuals[:, i], 1)
    daily_ma[0] = np.nan

    # ----------------------------
    # INTRADAY MA(1): eps[t, i-1]
    # ----------------------------
    if i == 0:
        intra_ma = np.zeros(T)
    else:
        intra_ma = residuals[:, i-1]

    # ----------------------------
    # LAGGED RAMP FEATURE
    # ramp[t] = y[t-1, i] - y[t-1, i-1]
    # ----------------------------
    if i == 0:
        lagged_ramp = np.zeros(T)
    else:
        prev_interval = y_panel[:, i] - y_panel[:, i-1]
        lagged_ramp = np.roll(prev_interval, 1)
        lagged_ramp[0] = np.nan

    # ----------------------------
    # BUILD FEATURE MATRIX
    # ----------------------------
    X = np.column_stack([
        daily_ar,
        intra_ar,
        season,
        daily_ma,
        intra_ma,
        lagged_ramp      # NEW FEATURE
    ])

    mask = np.isfinite(y) & np.all(np.isfinite(X), axis=1)

    return y[mask], X[mask], mask

@dataclass
class MeanFitResult:
    betas: list               # length I, each beta vector
    residuals: np.ndarray     # shape (T, I)

@dataclass
class MLMeanFitResult:
    models: list
    residuals: np.ndarray


def fit_iterated_intraday_arma(
    y_panel: np.ndarray,
    season: np.ndarray,
    n_iterations: int = 50,
    min_obs: int = 30,
) -> MeanFitResult:

    """
    Fits per-interval regression models, iterating residuals like MATLAB.
    """

    T, I = y_panel.shape
    tol = 1e-5
    residuals = np.zeros((T, I))
    betas = [None] * I

    for it in range(n_iterations):
        fitted = np.full((T, I), np.nan)

        for i in range(I):
            y_i, X_i, mask = build_mean_features(y_panel, season, residuals, i)

            if len(y_i) < min_obs:
                continue

            beta_i, yhat_i = fit_ols(y_i, X_i)
            betas[i] = beta_i
            fitted[mask, i] = yhat_i

        new_residuals = y_panel - fitted
        new_residuals[np.isnan(new_residuals)] = 0.0

        change = np.linalg.norm(
            new_residuals - residuals
        ) / np.linalg.norm(residuals + 1e-8)

        print(f"Iteration {it}, change={change:.6f}")
        if change < tol:
            print("Converged.")
            break
        residuals = new_residuals

    return MeanFitResult(betas=betas, residuals=residuals)


def fit_lightgbm_intraday_mean(
    y_panel: np.ndarray,
    season: np.ndarray,
    n_estimators: int = 300,
    learning_rate: float = 0.05,
):
    """
    Replace OLS mean with LightGBM per interval.
    """

    T, I = y_panel.shape
    residuals = np.zeros((T, I))
    models = []

    for i in range(I):

        y_i, X_i, mask = build_mean_features(
            y_panel,
            season,
            residuals,
            i
        )

        if len(y_i) < 30:
            models.append(None)
            continue

        model = lgb.LGBMRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=6,
            num_leaves=31
        )

        model.fit(X_i, y_i)

        # store model
        models.append(model)

        # compute fitted
        yhat = model.predict(X_i)

        full_fit = np.full(T, np.nan)
        full_fit[mask] = yhat

        residuals[:, i] = y_panel[:, i] - full_fit

    return MLMeanFitResult(
        models=models,
        residuals=residuals
    )

def forecast_next_day_mean(
    y_last_day: np.ndarray,
    season_next_day: np.ndarray,
    residuals_last_day: np.ndarray,
    residuals_prev_day: np.ndarray,
    betas: list,
    realized_today: np.ndarray | None = None,
):
    """
    Sequential intraday forecast.

    Parameters
    ----------
    y_last_day : array (I,)
        Observed generation for day t.

    season_next_day : array (3,)
        Seasonal dummies for day t+1.

    residuals_last_day : array (I,)
        eps[t, i]

    residuals_prev_day : array (I,)
        eps[t-1, i]

    betas : list
        Estimated coefficient vector per interval.

    realized_today : array (I,) or None
        If provided → intraday updating mode
        If None → open-loop day-ahead forecast

    Returns
    -------
    mean_forecast : array (I,)
        Forecasted generation for day t+1.
    """

    n_intervals = len(betas)
    mean_forecast = np.zeros(n_intervals)

    for i in range(n_intervals):
        if i == 0:
            pass
        beta_i = betas[i]

        if beta_i is None:
            mean_forecast[i] = np.nan
            continue

        # --------------------------------------------------
        # DAILY AR TERM
        # y[t, i]
        # --------------------------------------------------
        daily_ar = y_last_day[i]

        # --------------------------------------------------
        # INTRADAY AR TERM
        # y[t+1, i-1]
        # --------------------------------------------------
        if i == 0:
            intraday_ar = 0.0
        else:
            if realized_today is not None:
                # Intraday updating (MATLAB behaviour)
                intraday_ar = realized_today[i - 1]
            else:
                # Open-loop forecast
                intraday_ar = mean_forecast[i - 1]

        # --------------------------------------------------
        # DAILY MA TERM
        # eps[t-1, i]
        # --------------------------------------------------
        daily_ma = residuals_prev_day[i]

        # --------------------------------------------------
        # INTRADAY MA TERM
        # eps[t, i-1]
        # --------------------------------------------------
        intraday_ma = (
            residuals_last_day[i - 1] if i > 0 else 0.0
        )

        # --------------------------------------------------
        # LAGGED RAMP RATES
        # --------------------------------------------------

        if i == 0:
            lagged_ramp = 0.0
        else:
            lagged_ramp = y_last_day[i] - y_last_day[i - 1]

        # --------------------------------------------------
        # BUILD REGRESSOR VECTOR
        # --------------------------------------------------
        x = np.array([
            1.0,                     # intercept
            daily_ar,
            intraday_ar,
            *season_next_day,
            daily_ma,
            intraday_ma,
            lagged_ramp
        ])

        # --------------------------------------------------
        # FORECAST
        # --------------------------------------------------

        mean_forecast[i] = np.dot(beta_i, x)

    return mean_forecast


def forecast_next_day_mean_ml(
    y_last_day: np.ndarray,
    season_next_day: np.ndarray,
    residuals_last_day: np.ndarray,
    residuals_prev_day: np.ndarray,
    models: list,
    realized_today: np.ndarray | None = None,
):
    """
    Sequential intraday forecast using LightGBM models.
    """

    I = len(models)
    mean_forecast = np.zeros(I)

    for i in range(I):

        model = models[i]

        if model is None:
            mean_forecast[i] = np.nan
            continue

        daily_ar = y_last_day[i]

        if i == 0:
            intraday_ar = 0.0
        else:
            if realized_today is not None:
                intraday_ar = realized_today[i - 1]
            else:
                intraday_ar = mean_forecast[i - 1]

        daily_ma = residuals_prev_day[i]
        intraday_ma = residuals_last_day[i - 1] if i > 0 else 0.0

        if i == 0:
            lagged_ramp = 0.0
        else:
            lagged_ramp = y_last_day[i] - y_last_day[i - 1]

        x = np.array([
            daily_ar,
            intraday_ar,
            *season_next_day,
            daily_ma,
            intraday_ma,
            lagged_ramp
        ])


        # reshape for LightGBM
        mean_forecast[i] = model.predict(
            x.reshape(1, -1)
        )[0]

    return mean_forecast


def fit_garch_panel(residuals: np.ndarray):

    T, I = residuals.shape
    models = []

    for i in range(I):

        e = residuals[:, i]

        e = e[np.isfinite(e)]

        if len(e) < 40:
            models.append(None)
            continue

        am = arch_model(
            e,
            mean="Zero",
            vol="GARCH",
            p=1,
            q=1,
            dist="t"
        )

        res = am.fit(disp="off")
        models.append(res)

    return models

def forecast_garch_sigma(garch_models):

    sigma_next = []

    for model in garch_models:

        if model is None:
            sigma_next.append(np.nan)
            continue

        f = model.forecast(horizon=1)
        sigma_next.append(
            np.sqrt(f.variance.values[-1, 0])
        )

    return np.array(sigma_next)