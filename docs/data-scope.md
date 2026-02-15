# Data Scope: Wind and Solar (WEM & NEM)

## Objective

The objective of this document is to ensure that wind and solar data are clearly **scoped** by defining where the data comes from, how often it is observed, and the quality standards applied, so that reliable analysis and forecasting can be conducted.

For each signal (wind and solar), this document defines:

- **Data types** – Primary (raw outputs, prices) and derived (rolling statistics, ramps, calculated fields)
- **Data sources** – Authoritative APIs, public datasets, and modelled or simulated data
- **Temporal coverage** – Historical and near-real-time (e.g. 5-minute, 30-minute); forecast horizons: intraday, day-ahead, multi-day
- **Granularity** – Time, spatial, and technology resolution
- **Data quality** – Completeness thresholds, alignment, consistency, and timeliness (latency)
- **Ingestion rules** – Polling frequency, backfilling logic, versioning, and audit trails
- **Storage & retention** – Immutable raw data, cleaned/feature tables, defined retention periods
- **Constraints & exclusions** – Non-public data, known gaps or unreliable periods, regulatory or licensing limits

This document is the **authoritative data-scope reference**. All ingestion, modelling, and validation components must conform to this definition.

---

## Wind Data

### Data Type

Facility-level generation with the following attributes:
- Technology type: Wind
- Operating status: Operating, Committed, Retired
- Facility size classification:  
  < 1 MW, 1–5 MW, 5–30 MW, > 30 MW

---

### Wind Facility Generation (WEM)

The following wind facilities are currently in scope for the WEM. This list reflects current coverage and may expand as additional facilities are added.

- Waddi – `0WADDIWF1`
- Flat Rocks – `FLATROCKS_WF1`
- Kings Rock – `0KINGS_ROCK_WF`
- Bero Road – `BLAIRFOX_BEROSRD_WF1`
- Albany – `ALBANY_WF1`
- Badgingarra – `BADGINGARRA_WF1`
- Bremer Bay – `BREMER_BAY_WF1`
- Collgar – `INVESTEC_COLLGAR_WF1`
- Denmark – `DCWL_DENMARK_WF1`
- Emu Downs – `EDWFMAN_WF1`
- Grasmere – `GRASMERE_WF1`
- Kalbarri – `KALBARRI_WF1`
- Karakin – `BLAIRFOX_KARAKIN_WF1`
- Mount Barker – `SKYFRM_MTBARKER_WF1`
- Mumbida – `MWF_MUMBIDA_WF1`
- Walkaway – `ALINTA_WWF`
- West Hills – `BLAIRFOX_WESTHILLS_WF3`
- Yandin – `YANDIN_WF1`
- Warradarge – `WARRADARGE_WF1`, `0WARRADARGE_WF2`

---

## Solar Data

### Solar Facility Generation (WEM)

The following solar facilities are currently in scope for the WEM. This list is not exhaustive.

- Cunderdin – `SBSOLAR1_CUNDERDIN_PV1`
- Greenough River – `GREENOUGH_RIVER_PV1`
- Metro – `AMBRISOLAR_PV1`
- Northam – `NORTHAM_SF_PV1`
- Merredin – `MERSOLAR_PV1`

---

## Facility Metadata

For each facility, the following metadata is included:

- **Registered Capacity** – The maximum electrical output (MW) formally registered with AEMO

---

## Data Sources

- **Authoritative source of truth:** AEMO (NEM and WEM)
- **Access layer:** Open Electricity, which exposes and enhances public AEMO records

Open Electricity does not create the data; it derives from public AEMO datasets.

Source:
https://explore.openelectricity.org.au/facilities/wem/

---

## Temporal Coverage and Granularity

- **Interval resolution:**
  - 5-minute dispatch intervals (native ingestion)
  - 30-minute trading intervals (aggregation)
- **Trading day:** 08:00 to 07:30 the following day
- **Spatial coverage:** Facility-level with aggregation to region and system
- **Historical coverage:**
  - WEM: From 30 October 2023 to present
  - NEM: From 2009 to present

The historical start dates reflect public data availability and consistency.

---

## Data Quality Definition

Data quality is primarily assessed through **completeness**, with additional validation on alignment, bounds, and internal consistency.

---

## Decisions Supported

This data supports:

- Short-term and medium-term forecasting for wind and solar generation
- Real-time situational awareness of current generation
- Historical analysis for model training, validation, and back-testing
- A public-facing web application showing:
  - Current generation
  - Historical performance
  - Forward-looking forecasts

**Implication:**  
Data must be fresh, re-runnable, and revision-aware. Provisional data is acceptable but must be clearly flagged.

---

## Market Clock

- Trading day runs from 08:00 to 07:30 the following day
- Settlement and reporting align to the trading day
- Data is published on fixed interval grids:
  - 5-minute dispatch intervals
  - 30-minute trading intervals

Completeness checks must be based on trading-day boundaries and expected interval counts.

---

## Granularity Requirements

- Native ingestion at 5-minute resolution
- 30-minute data derived via aggregation
- Hierarchical reconciliation supported:
  - 5-minute to 30-minute
  - Facility to region to system

Raw 5-minute data must be preserved and never overwritten by aggregates.

---

## Data Revisions

- Actual generation values may be revised after publication
- Metadata such as registered or nameplate capacity may also change, less frequently

Ingestion must re-ingest recent history, allow updates to existing records, and distinguish provisional from revised data.

---

## Definition of Bad Data

Bad data includes:

- Missing dispatch or trading intervals
- Null or non-finite values
- Misaligned timestamps
- 30-minute aggregates that do not equal summed 5-minute data
- Values exceeding physical or registered capacity bounds (where known)

Bad data must be detected and flagged, not silently corrected.

---

## Downstream Guarantees

Users can expect:

- A current snapshot of wind and solar generation
- Consistent and reproducible historical data
- Forecasts aligned with training data
- Transparency when data is provisional, missing, or estimated

Ingestion must prioritise idempotency, traceability, and data freshness indicators.

---

## Failure Modes

- Partial ingestion is acceptable if clearly flagged
- Silent failure is not acceptable
- Missing intervals are acceptable if visible
- Corrupt or misaligned data must be rejected
- The system must always be safe to re-run

The system should fail loudly but safely.

---

## Storage & Retention

- Raw source data is stored in an immutable format for reproducibility
- Cleaned, canonical time-series data is stored in a database
- Derived data may be retained for a limited period and recomputed

### Retention Periods

| Data Type | Retention |
|---------|-----------|
| Raw source data | Indefinite |
| Canonical actuals | Indefinite |
| Aggregates (30-min) | Indefinite |
| Forecast outputs | 6–24 months |
| Logs / run metadata | 30–90 days |

---

## Constraints & Exclusions

- Only public, non-confidential data is used; private SCADA, bids, or telemetry are excluded
- Known data gaps or unreliable periods are not filled silently and are explicitly flagged
- Data usage is subject to regulatory, licensing, and source-specific limitations

