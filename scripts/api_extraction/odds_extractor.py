import requests
import pandas as pd
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()


class OddsAPIExtractor:
    """
    Extractor for The Odds API focused on Betway bookmaker odds.
    Extracts exhaustive markets (h2h, spreads, totals, etc.) for multiple soccer leagues.
    
    Supported Sports:
    - soccer_epl: English Premier League
    - soccer_la_liga: Spanish La Liga
    - soccer_serie_a: Italian Serie A
    - soccer_uefa_champs_league: UEFA Champions League
    
    Supported Markets (available from The Odds API for Betway):
    - h2h: Head-to-head (match winner)
    - spreads: Point spreads
    - totals: Total goals over/under
    """

    # Soccer leagues to extract (mapped to sport keys)
    SOCCER_LEAGUES = {
        'soccer_epl': 'English Premier League (EPL)',
        'soccer_la_liga': 'Spanish La Liga',
        'soccer_serie_a': 'Italian Serie A',
        'soccer_uefa_champs_league': 'UEFA Champions League'
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the extractor with API key"""
        if api_key is None:
            api_key = os.getenv('ODDS_API_KEY')
        
        if not api_key:
            raise ValueError("ODDS_API_KEY not found in environment variables!")
        
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.requests_remaining = None
        self.extraction_summary = []

    def get_available_sports(self) -> Optional[List[Dict]]:
        """Get list of available sports from The Odds API"""
        url = f"{self.base_url}/sports/"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            sports = response.json()
            self._update_requests_remaining(response)
            
            print(f"[OK] Retrieved {len(sports)} total sports")
            print(f"[INFO] Requests remaining: {self.requests_remaining}")
            
            return sports
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching sports: {e}")
            return None

    def _update_requests_remaining(self, response: requests.Response) -> None:
        """Update remaining API requests from response headers"""
        self.requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')

    def extract_odds_for_leagues(
        self, 
        leagues: Optional[List[str]] = None,
        regions: List[str] = ['uk', 'us'],
        bookmakers: List[str] = ['betway']
    ) -> pd.DataFrame:
        """
        Extract odds for multiple soccer leagues with all available markets.
        
        Args:
            leagues: List of league keys (default: all supported leagues)
            regions: Regions to include (default: ['uk', 'us'])
            bookmakers: Bookmakers to filter (default: ['betway'])
        
        Returns:
            Combined DataFrame with all extracted odds
        """
        if leagues is None:
            leagues = list(self.SOCCER_LEAGUES.keys())
        
        # Validate leagues
        leagues = [l for l in leagues if l in self.SOCCER_LEAGUES]
        
        if not leagues:
            print("[ERROR] No valid leagues specified. Use one of:")
            for key, name in self.SOCCER_LEAGUES.items():
                print(f"   - {key}: {name}")
            return pd.DataFrame()
        
        all_data = []
        
        print(f"\n{'='*70}")
        print(f"EXTRACTING ODDS FOR {len(leagues)} SOCCER LEAGUES")
        print(f"{'='*70}\n")
        
        for league_key in leagues:
            league_name = self.SOCCER_LEAGUES[league_key]
            print(f"[LEAGUE] Extracting: {league_name}")
            print(f"         Sport Key: {league_key}")
            
            # Extract with all available markets
            raw_data = self.extract_odds(
                sport_key=league_key,
                bookmakers=bookmakers,
                regions=regions,
                markets=None  # None = all available markets
            )
            
            if raw_data:
                df = self.transform_to_dataframe(raw_data, league_key)
                if not df.empty:
                    all_data.append(df)
                    self.extraction_summary.append({
                        'league': league_name,
                        'league_key': league_key,
                        'matches': len(raw_data),
                        'records': len(df),
                        'extracted_at': datetime.now(timezone.utc).isoformat()
                    })
            
            print()
        
        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"{'='*70}")
            print(f"[OK] EXTRACTION COMPLETE")
            print(f"{'='*70}")
            print(f"Total Leagues: {len(leagues)}")
            print(f"Total Records: {len(combined_df)}")
            print(f"Requests Remaining: {self.requests_remaining}\n")
            return combined_df
        else:
            print("[WARNING] No data extracted")
            return pd.DataFrame()

    def extract_odds(
        self, 
        sport_key: str, 
        bookmakers: List[str] = ['betway'], 
        regions: List[str] = ['uk', 'us'],
        markets: Optional[List[str]] = None
    ) -> Optional[List[Dict]]:
        """
        Extract odds for a specific sport with exhaustive markets.
        
        Args:
            sport_key: Sport key (e.g., 'soccer_epl')
            bookmakers: List of bookmakers to filter (default: ['betway'])
            regions: Regions to include (default: ['uk', 'us'])
            markets: Markets to retrieve. If None, fetches all available markets
        
        Returns:
            Raw API response data or None on error
        """
        url = f"{self.base_url}/sports/{sport_key}/odds/"
        
        # If no markets specified, request all available markets
        # Common markets: h2h, spreads, totals
        if markets is None:
            markets = ['h2h', 'spreads', 'totals']
        
        params = {
            'apiKey': self.api_key,
            'regions': ','.join(regions),
            'markets': ','.join(markets),
            'bookmakers': ','.join(bookmakers),
            'oddsFormat': 'decimal'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            self._update_requests_remaining(response)
            
            print(f"   [OK] {len(data)} matches found")
            print(f"        Markets requested: {', '.join(markets)}")
            print(f"        Requests remaining: {self.requests_remaining}")
            
            return data
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print(f"   [ERROR] Authentication Error: Invalid API Key")
            elif response.status_code == 429:
                print(f"   [ERROR] Rate Limit Error: No requests remaining")
            else:
                print(f"   [ERROR] HTTP Error {response.status_code}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"   [ERROR] Connection Error: {e}")
            return None

    def transform_to_dataframe(self, raw_data: List[Dict], sport_key: str = '') -> pd.DataFrame:
        """
        Transform raw API data to structured DataFrame with all markets.
        
        Args:
            raw_data: Raw API response data
            sport_key: Sport key for reference
        
        Returns:
            Pandas DataFrame with flattened market data
        """
        records = []
        
        for game in raw_data:
            game_id = game['id']
            home_team = game['home_team']
            away_team = game['away_team']
            commence_time = game['commence_time']
            
            # Process each bookmaker (typically just Betway)
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] != 'betway':
                    continue
                
                bookmaker_key = bookmaker['key']
                
                # Process each market (h2h, spreads, totals, etc.)
                for market in bookmaker.get('markets', []):
                    market_type = market['key']  # e.g., 'h2h', 'spreads', 'totals'
                    
                    # Process each outcome/outcome in the market
                    for outcome in market.get('outcomes', []):
                        record = {
                            'game_id': game_id,
                            'sport_key': sport_key or game.get('sport_key', ''),
                            'sport_title': game.get('sport_title', ''),
                            'home_team': home_team,
                            'away_team': away_team,
                            'commence_time': commence_time,
                            'bookmaker': bookmaker_key,
                            'market_type': market_type,
                            'outcome_name': outcome['name'],
                            'odds': outcome['price'],
                            'point': outcome.get('point', None),  # For spreads/totals
                            'extracted_at': datetime.now(timezone.utc).isoformat()
                        }
                        records.append(record)
        
        if records:
            df = pd.DataFrame(records)
            print(f"   [OK] Transformed {len(records)} records")
            return df
        else:
            print(f"   [WARNING] No Betway odds found to transform")
            return pd.DataFrame()

    def save_to_csv(self, df: pd.DataFrame, filename: str = 'odds_data') -> Optional[str]:
        """
        Save DataFrame to CSV file with timestamp.
        
        Args:
            df: Pandas DataFrame to save
            filename: Base filename (timestamp will be appended)
        
        Returns:
            Full filepath where file was saved, or None if empty
        """
        if df.empty:
            print("[WARNING] Cannot save empty DataFrame")
            return None
        
        os.makedirs('data/raw', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = f"data/raw/{filename}_{timestamp}.csv"
        
        try:
            df.to_csv(filepath, index=False)
            print(f"[OK] Saved {len(df)} records to {filepath}")
            return filepath
        except Exception as e:
            print(f"[ERROR] Error saving file: {e}")
            return None

    def print_extraction_summary(self) -> None:
        """Print summary of all extractions"""
        if not self.extraction_summary:
            return
        
        print(f"\n{'='*70}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*70}")
        print(f"{'League':<35} {'Matches':<12} {'Records':<12}")
        print(f"{'-'*70}")
        
        for item in self.extraction_summary:
            league_name = item['league'][:32]  # Truncate for display
            matches = item['matches']
            records = item['records']
            print(f"{league_name:<35} {matches:<12} {records:<12}")
        
        print(f"{'='*70}\n")


# Example usage
if __name__ == "__main__":
    print("\n" + "="*70)
    print("ODDS API - MULTI-LEAGUE EXHAUSTIVE MARKETS EXTRACTOR")
    print("="*70 + "\n")
    
    try:
        # Initialize extractor
        extractor = OddsAPIExtractor()
        print("[OK] Extractor initialized successfully\n")
        
        # Extract odds for all supported leagues with all markets
        combined_df = extractor.extract_odds_for_leagues(
            leagues=['soccer_epl', 'soccer_la_liga', 'soccer_serie_a', 'soccer_uefa_champs_league']
        )
        
        # Print summary
        extractor.print_extraction_summary()
        
        # Save to CSV
        if not combined_df.empty:
            filepath = extractor.save_to_csv(combined_df, 'betway_exhaustive_markets')
            
            # Display sample data
            print("\n" + "="*70)
            print("SAMPLE DATA (First 10 Records)")
            print("="*70)
            print(combined_df.head(10).to_string())
            print(f"\nDataFrame shape: {combined_df.shape}")
            print(f"Markets present: {combined_df['market_type'].unique().tolist()}")
            print(f"Leagues present: {combined_df['sport_key'].unique().tolist()}")
        else:
            print("[WARNING] No data to display")
    
    except ValueError as e:
        print(f"[ERROR] Configuration Error: {e}")
        print("        Please ensure ODDS_API_KEY is set in your .env file")
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
