{{ config(
    materialized='table',
    schema='gold',
    tags=['marts', 'analytics', 'match_details']
) }}

SELECT
    game_id,
    match_date,
    match_hour_utc,
    sport_key,
    sport_title,
    home_team,
    away_team,
    commence_time,
    -- H2H Odds
    home_win_odds,
    away_win_odds,
    draw_odds,
    -- Probabilities
    home_win_implied_prob,
    away_win_implied_prob,
    draw_implied_prob,
    -- Metrics
    bookmaker_margin_h2h,
    neutral_home_prob,
    -- Other Markets
    home_spread_odds,
    away_spread_odds,
    over_odds,
    under_odds,
    -- Metadata
    ingestion_date,
    extracted_at,
    dbt_loaded_at,
    dbt_transformed_at,
    CURRENT_TIMESTAMP() as record_generated_at
FROM {{ ref('int_odds_with_margins') }}
WHERE home_win_odds IS NOT NULL
ORDER BY commence_time DESC, sport_key
