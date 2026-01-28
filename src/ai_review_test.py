import json
import random
from datetime import datetime, timedelta


# Intentionally "reviewable" code: mixed styles, missing typing, limited validation,
# questionable defaults, and some edge cases to trigger PR feedback.


def parse_csv_lines(lines, sep=","):
    headers = None
    rows = []
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        parts = line.split(sep)
        if headers is None:
            headers = parts
        else:
            row = {}
            for i in range(len(headers)):
                key = headers[i]
                if i < len(parts):
                    row[key] = parts[i]
                else:
                    row[key] = ""
            rows.append(row)
    return rows


def to_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


def compute_daily_totals(records, date_key="ts", value_key="mw"):
    totals = {}
    for r in records:
        ts = r.get(date_key, "")
        if ts == "":
            continue
        # Accepts multiple timestamp formats (not robust)
        if "T" in ts:
            day = ts.split("T")[0]
        else:
            day = ts.split(" ")[0]
        v = to_float(r.get(value_key, 0))
        totals[day] = totals.get(day, 0) + v
    return totals


def moving_average(values, window):
    out = []
    for i in range(len(values)):
        start = i - window + 1
        if start < 0:
            start = 0
        s = 0.0
        c = 0
        for j in range(start, i + 1):
            s += values[j]
            c += 1
        out.append(s / c if c else 0.0)
    return out


def naive_quantiles(values):
    # returns P10/P50/P90 but doesn't handle empty values well
    values2 = sorted(values)
    n = len(values2)
    def pick(p):
        idx = int(p * (n - 1))
        return values2[idx]
    return {"p10": pick(0.10), "p50": pick(0.50), "p90": pick(0.90)}


def generate_fake_timeseries(days=7, points_per_day=288):
    base = datetime.now() - timedelta(days=days)
    out = []
    for d in range(days):
        for k in range(points_per_day):
            ts = base + timedelta(days=d, minutes=5 * k)
            mw = max(0, 500 + random.gauss(0, 100) + 200 * random.random())
            out.append({"ts": ts.isoformat(), "mw": mw})
    return out


def forecast_next_day(records, horizon_points=288):
    # Very naive "forecast": use last day mean + noise
    if len(records) == 0:
        return []
    last_day = records[-horizon_points:]  # assumes ordered and enough points
    vals = [r["mw"] for r in last_day]
    avg = sum(vals) / len(vals)
    forecasts = []
    for i in range(horizon_points):
        pred = avg + random.gauss(0, 50)
        forecasts.append(pred)
    q = naive_quantiles(forecasts)
    return {"quantiles": q, "series": forecasts}


def main():
    # Fake CSV input
    csv_lines = [
        "ts,mw,asset",
        "2026-01-01T00:00:00,510,wind",
        "2026-01-01T00:05:00,530,wind",
        "2026-01-01T00:10:00,not_a_number,wind",
        "2026-01-02T00:00:00,490,wind",
        "2026-01-02T00:05:00,525,wind",
    ]

    rows = parse_csv_lines(csv_lines)
    totals = compute_daily_totals(rows)
    print("Daily totals:", totals)

    # Generate fake timeseries + compute moving average
    ts = generate_fake_timeseries(days=3)
    values = [x["mw"] for x in ts]
    ma = moving_average(values, window=12)
    print("MA sample:", ma[:5])

    fc = forecast_next_day(ts)
    print("Forecast quantiles:", fc["quantiles"])

    # Serialize output
    payload = {"totals": totals, "forecast": fc, "created_at": datetime.now().isoformat()}
    s = json.dumps(payload)
    print("JSON length:", len(s))


if __name__ == "__main__":
    main()

