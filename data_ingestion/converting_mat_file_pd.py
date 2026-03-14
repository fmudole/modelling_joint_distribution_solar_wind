from datetime import datetime, timezone, timedelta
import pandas as pd
import scipy.io
import numpy as np

UTC_PLUS_10 = timezone(timedelta(hours=10))


def make_timstamp_plus10(year, month, day, hour, minute, second):
    return datetime(
        int(year),
        int(month),
        int(day),
        int(hour),
        int(minute),
        int(second),
        tzinfo=UTC_PLUS_10
    ).isoformat(timespec="seconds")


def make_30min_timestamps_20_per_day(start_date: str, ndays: int = 883) -> np.ndarray:

    """
    20 timestamps per day at 30-min spacing:
    07:00, 07:30, ..., 16:30 (i.e., 20 points)
    Timezone fixed at +10:00.

    start_date: "YYYY-MM-DD"
    returns: 1-D numpy array of RFC3339 strings
    """

    start_day = datetime.fromisoformat(start_date).date()
    out = []

    for d in range(ndays):
        day = start_day + timedelta(days=d)
        day_start = datetime(day.year, day.month, day.day, 7, 0, 0, tzinfo=UTC_PLUS_10)

        for k in range(20):  # 20 intervals
            dt = day_start + timedelta(minutes=30 * k)
            out.append(dt.isoformat(timespec="seconds"))

    return np.array(out, dtype=object)


def convert_mat_to_pd(mat: dict, fueltech: str, region: str) -> pd.DataFrame:

    yr_start = mat["yr"].ravel()[0]
    mth_start = mat["mth"].ravel()[0]
    hr_start = mat["hr"].ravel()[0]
    mn_start = mat["min"].ravel()[0]
    sec_start = mat["sec"].ravel()[0]

    num_days = mat["ndays"][0, 0]
    start_date = make_timstamp_plus10(yr_start, mth_start, 1, hr_start, mn_start, sec_start)

    timestamps = make_30min_timestamps_20_per_day(start_date=start_date, ndays=num_days)

    n = len(timestamps)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "region": [region] * n,
        "fueltech": [fueltech] * n,
        "metric": ["MW"] * n
    })

    if "data_tmp" in mat:
        data =mat["data_tmp"].ravel()
        df["value"] = data

    return df

# load files


if __name__ == "__main__":

    qld_mat_solar = scipy.io.loadmat("data/QLD_fullPV.mat")
    qld_mat_wind = scipy.io.loadmat("data/QLD_fullW.mat")
    sa_mat_solar = scipy.io.loadmat("data/SA_fullPV.mat")
    sa_mat_wind = scipy.io.loadmat("data/SA_fullW.mat")

    def convert_pd_csv():
        df = pd.concat([
            convert_mat_to_pd(sa_mat_solar, fueltech="solar", region="SA1"),
            convert_mat_to_pd(sa_mat_wind, fueltech="wind", region="SA1"),
            convert_mat_to_pd(qld_mat_wind, fueltech="wind", region="QLD1"),
            convert_mat_to_pd(qld_mat_solar, fueltech="solar", region="QLD1"),
        ], ignore_index=True)

        df.to_csv(
            "data/wind_solar_qld_sa_adam_clement_data.csv",
            index=False
        )

    convert_pd_csv()