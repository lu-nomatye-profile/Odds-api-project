{{ config(
    materialized='table',
    schema='gold',
    tags=['marts', 'analytics', 'daily_summary']
) }}

SELECT
    match_date,
    sport_title,
    sport_key,
    COUNT(DISTINCT game_id) as total_matches,
    COUNT(DISTINCT home_team) as unique_home_teams,
    COUNT(DISTINCT away_team) as unique_away_teams,
    ROUND(AVG(home_win_odds), 2) as avg_home_win_odds,
    ROUND(AVG(away_win_odds), 2) as avg_away_win_odds,
    ROUND(AVG(draw_odds), 2) as avg_draw_odds,
    ROUND(MIN(home_win_odds), 2) as min_home_win_odds,
    ROUND(MAX(home_win_odds), 2) as max_home_win_odds,
    ROUND(AVG(bookmaker_margin_h2h), 4) as avg_bookmaker_margin,
    ROUND(MIN(bookmaker_margin_h2h), 4) as min_bookmaker_margin,
    ROUND(MAX(bookmaker_margin_h2h), 4) as max_bookmaker_margin,
    ROUND(AVG(home_win_implied_prob), 4) as avg_home_win_implied_prob,
    ROUND(AVG(away_win_implied_prob), 4) as avg_away_win_implied_prob,
    MIN(commence_time) as earliest_kickoff,
    MAX(commence_time) as latest_kickoff,
    MAX(ingestion_date) as latest_data_date,
    CURRENT_TIMESTAMP() as report_generated_at
FROM {{ ref('int_odds_with_margins') }}
WHERE home_win_odds IS NOT NULL
AND away_win_odds IS NOT NULL
AND draw_odds IS NOT NULL
GROUP BY match_date, sport_title, sport_key
ORDER BY match_date DESC, sport_title
