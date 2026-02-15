from datetime import datetime, timedelta
from openelectricity import OEClient
from openelectricity.types import DataMetric
import pandas as pd

MAX_API_DAY = 7

import logging
import os
import psycopg2

from psycopg2.extras import execute_batch

MAX_API_DAY = 7


class SDKConfig:
    def __init__(self,
                 api_key: str | None = None,
                 log_level: int = logging.INFO):
        self.api_key = api_key or os.getenv("OPENELECTRICITY_API_KEY")
        self.log_level = log_level

        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("forecasting_sdk")
        self.logger.setLevel(self.log_level)
        if not self.logger.hasHandlers():
            ch = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

#
class ForecastingCoreClient:
    def __init__(self, config):
        self.config = config
        self.logger = getattr(config, "logger", None)

    def fetch_data(
        self,
        start_date: datetime,
        end_date: datetime,
        network_code: list[str] = ["NEM", "WEM"],
        metrics: list[DataMetric] = [DataMetric.POWER],
        interval: str = "5m",
        primary_grouping: str = "network_region",
        secondary_grouping: str = "fueltech_group",
    ) -> pd.DataFrame:

        total_data = []
        current_start = start_date
        for net_work in network_code:
            with OEClient(api_key=self.config.api_key) as client:
                while current_start < end_date:
                    current_end = min(
                        current_start + timedelta(MAX_API_DAY),
                        end_date
                    )

                    response_data = client.get_network_data(
                        network_code=net_work,
                        metrics=metrics,
                        interval=interval,
                        date_start=current_start,
                        date_end=current_end,
                        primary_grouping=primary_grouping,
                        secondary_grouping=secondary_grouping,
                    )

                    total_data.append(response_data)
                    current_start = current_end

            if not total_data:
                return pd.DataFrame()

        return pd.concat(total_data, ignore_index=True)

    def fetch_latest_7days(self, **kwargs) -> pd.DataFrame:
        end_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_date = end_date - timedelta(days=7)

        return self.fetch_data(start_date, end_date, **kwargs)

    def fetch_last_365_days(self, **kwargs) -> pd.DataFrame:
        end_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_date = end_date - timedelta(days=365)

        return self.fetch_data(start_date, end_date, **kwargs)

def get_db_connection():
    return psycopg2.connect(
            dbname=os.environ["POSTGRES_DB_NAME"],
            user=os.environ["POSTGRES_DB_USER"],
            password=os.environ["POSTGRES_DB_PASSWORD"],
            host=os.environ["POSTGRES_DB_HOST"],
            port=os.environ["POSTGRES_DB_PORT"],
        )

con = get_db_connection()

def store_to_db(df):
    conn = get_db_connection()
    cur = conn.cursor()
    insert_query = """
          INSERT INTO network_measurements_mw
          (timestamp, network_code, fueltech, region, facility_code,
           value_mw, inserted_at)
          VALUES (%s, %s, %s, %s, %s, %s, %s)
          ON CONFLICT (timestamp, series_key)
          DO UPDATE SET value_mw = EXCLUDED.value_mw;
      """

    rows = []
    for _, row in df.iterrows():
        network_code = row["network_code"]
        rows.append((
            row["timestamp"],
            network_code,
            row["fueltech"],
            row["region"],
            row.get("facility_code"),
            row["value"],
            datetime.utcnow()))

    execute_batch(cur, insert_query, rows)

    conn.commit()
    cur.close()
    conn.close()

    print("Successfully stored data to database")

def main():

    config = SDKConfig()
    forecaster = ForecastingCoreClient(config)

    data = forecaster.fetch_latest_7days()
    store_to_db(data)

if __name__ == "__main__":
    main()