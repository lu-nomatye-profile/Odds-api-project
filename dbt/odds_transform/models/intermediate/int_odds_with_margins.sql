{{ config(
    materialized='incremental',
    unique_key=['game_id', 'market_type'],
    schema='silver',
    tags=['intermediate', 'odds', 'calculations']
) }}

WITH odds_pivoted AS (
    SELECT
        game_id,
        sport_key,
        sport_title,
        home_team,
        away_team,
        commence_time,
        market_type,
        ingestion_date,
        -- Pivot outcomes by team for h2h market
        MAX(CASE WHEN outcome_name = home_team AND market_type = 'h2h' THEN odds END) as home_win_odds,
        MAX(CASE WHEN outcome_name = away_team AND market_type = 'h2h' THEN odds END) as away_win_odds,
        MAX(CASE WHEN outcome_name = 'Draw' AND market_type = 'h2h' THEN odds END) as draw_odds,
        -- Spreads
        MAX(CASE WHEN outcome_name LIKE CONCAT(home_team, '%') AND market_type = 'spreads' THEN odds END) as home_spread_odds,
        MAX(CASE WHEN outcome_name LIKE CONCAT(away_team, '%') AND market_type = 'spreads' THEN odds END) as away_spread_odds,
        -- Totals
        MAX(CASE WHEN outcome_name LIKE 'Over%' AND market_type = 'totals' THEN odds END) as over_odds,
        MAX(CASE WHEN outcome_name LIKE 'Under%' AND market_type = 'totals' THEN odds END) as under_odds,
        extracted_at,
        dbt_loaded_at
    FROM {{ ref('stg_odds_raw') }}
    GROUP BY 
        game_id, sport_key, sport_title, home_team, away_team, 
        commence_time, market_type, ingestion_date, extracted_at, dbt_loaded_at
),

odds_with_calculations AS (
    SELECT
        *,
        -- Implied probabilities (1/odds)
        CASE WHEN home_win_odds > 0 THEN ROUND(1.0 / home_win_odds, 4) ELSE NULL END as home_win_implied_prob,
        CASE WHEN away_win_odds > 0 THEN ROUND(1.0 / away_win_odds, 4) ELSE NULL END as away_win_implied_prob,
        CASE WHEN draw_odds > 0 THEN ROUND(1.0 / draw_odds, 4) ELSE NULL END as draw_implied_prob,
        -- Bookmaker margin (overround) for h2h market
        CASE WHEN home_win_odds > 0 AND away_win_odds > 0 AND draw_odds > 0 
            THEN ROUND(1.0/home_win_odds + 1.0/away_win_odds + 1.0/draw_odds - 1.0, 4)
            ELSE NULL 
        END as bookmaker_margin_h2h,
        -- Optimal neutral probability (equal stakes Kelly)
        CASE WHEN home_win_odds > 0 AND away_win_odds > 0 AND draw_odds > 0
            THEN ROUND(
                CASE WHEN 1.0/home_win_odds + 1.0/away_win_odds + 1.0/draw_odds > 0
                    THEN (1.0/home_win_odds) / (1.0/home_win_odds + 1.0/away_win_odds + 1.0/draw_odds)
                    ELSE NULL
                END, 4
            )
            ELSE NULL
        END as neutral_home_prob,
        -- Date time fields
        CAST(commence_time AS DATE) as match_date,
        HOUR(commence_time) as match_hour_utc
    FROM odds_pivoted
)

SELECT
    *,
    CURRENT_TIMESTAMP() as dbt_transformed_at
FROM odds_with_calculations

{% if is_incremental() %}
WHERE ingestion_date > (SELECT MAX(ingestion_date) FROM {{ this }})
{% endif %}
