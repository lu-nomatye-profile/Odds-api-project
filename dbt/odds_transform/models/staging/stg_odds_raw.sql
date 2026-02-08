{{ config(
    materialized='view',
    schema='silver',
    tags=['staging', 'odds']
) }}

SELECT
    game_id,
    sport_key,
    sport_title,
    home_team,
    away_team,
    CAST(commence_time AS TIMESTAMP) as commence_time,
    bookmaker,
    market_type,
    outcome_name,
    CAST(odds AS DECIMAL(10,4)) as odds,
    CAST(point AS DECIMAL(10,2)) as point,
    CAST(extracted_at AS TIMESTAMP) as extracted_at,
    ingestion_date,
    CAST(ingestion_timestamp AS TIMESTAMP) as ingestion_timestamp,
    CURRENT_TIMESTAMP() as dbt_loaded_at
FROM {{ source('bronze', 'odds_raw') }}
WHERE bookmaker = 'betway'
AND odds > 0
