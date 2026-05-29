{{ config(materialized='table') }}

SELECT
    reporting_date::DATE AS reporting_date,
    entity,
    cet1_capital_mm::DOUBLE AS cet1_capital_mm,
    rwa_mm::DOUBLE         AS rwa_mm,
    cet1_ratio_pct::DOUBLE AS cet1_ratio_pct,
    combined_buffer::DOUBLE AS combined_buffer
FROM (
    VALUES
        ('2025-09-30', 'BANK_HOLDCO', 27410.00, 190500.00, 14.39, 9.75),
        ('2025-12-31', 'BANK_HOLDCO', 28150.00, 192000.00, 14.66, 9.75),
        ('2026-03-31', 'BANK_HOLDCO', 29273.00, 197400.00, 14.83, 9.75)
) AS t(reporting_date, entity, cet1_capital_mm, rwa_mm, cet1_ratio_pct, combined_buffer)
