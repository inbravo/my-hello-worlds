{{ config(materialized='table') }}

-- MetricFlow time spine — required for time-based metric queries.
-- Covers the full range of the capital_position dataset plus buffer.
SELECT date_day
FROM (
    SELECT range::DATE AS date_day
    FROM range(
        '2025-01-01'::DATE,
        '2027-01-01'::DATE,
        INTERVAL '1 day'
    )
) AS spine
