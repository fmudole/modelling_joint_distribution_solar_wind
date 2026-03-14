import pandas as pd
import numpy as np

def prepare_generation_panel(
    df: pd.DataFrame,
    region: str = "SA1",
    fueltech: str = "wind"
) -> pd.DataFrame:
    """
    Convert long energy data into modelling panel:

    date | interval | generation | D_SU | D_AU | D_SP
    """

    # -------------------------------------------------
    # 1. Filter region + fueltech
    # -------------------------------------------------
    df = df.loc[
        (df["region"] == region) &
        (df["fueltech"] == fueltech)
    ].copy()

    if df.empty:
        raise ValueError("Filtered dataframe is empty.")

    # -------------------------------------------------
    # 2. Timestamp handling
    # -------------------------------------------------
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp")

    # -------------------------------------------------
    # 3. Extract date
    # -------------------------------------------------
    df["date"] = df["timestamp"].dt.date

    # -------------------------------------------------
    # 4. Create interval number
    # (30-min market → 48 intervals/day)
    # -------------------------------------------------
    df["interval"] = (
        df["timestamp"].dt.hour * 2
        + df["timestamp"].dt.minute // 30
        + 1
    )

    # -------------------------------------------------
    # 5. Generation column
    # -------------------------------------------------
    df["generation"] = df["value"].astype(float)

    # -------------------------------------------------
    # 6. Seasonal Dummies
    # -------------------------------------------------
    month = df["timestamp"].dt.month

    df["D_SU"] = month.isin([12, 1, 2]).astype(int)  # Summer
    df["D_AU"] = month.isin([3, 4, 5]).astype(int)   # Autumn
    df["D_WI"] = month.isin([6, 7, 8]).astype(int)   # Winter
    df["D_SP"] = month.isin([9, 10, 11]).astype(int) # Spring

    # Optional: drop one dummy to avoid multicollinearity
    df = df.drop(columns=["D_WI"])

    # -------------------------------------------------
    # 7. Final structure
    # -------------------------------------------------
    out = df[
        ["date", "interval", "generation", "D_SU", "D_AU", "D_SP"]
    ].reset_index(drop=True)

    return out

df = pd.read_csv("wind_solar_qld_sa_adam_clement_data.csv")
data = prepare_generation_panel(df=df)
