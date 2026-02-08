import requests
import pandas as pd
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OddsAPIExtractor:
    """Extractor for The Odds API - focusing on Betway bookmaker"""

    def __init__(self, api_key=None):
        """Initialize the extractor with API key"""
        if api_key is None:
            api_key = os.getenv('ODDS_API_KEY')
        
        if not api_key:
            raise ValueError("ODDS_API_KEY not found in environment variables!")
        
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

    def get_available_sports(self):
        """Get list of available sports from The Odds API"""
        url = f"{self.base_url}/sports/"
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            sports = response.json()
            print(f"✅ Retrieved {len(sports)} total sports")
            print(f"📊 Requests remaining: {response.headers.get('x-requests-remaining')}")
            
            return sports
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching sports: {e}")
            return None

    def extract_odds(self, sport_key, bookmakers=['betway'], markets=['h2h'], regions=['uk', 'us']):
        """
        Extract odds for a specific sport and bookmaker
        
        Args:
            sport_key: Sport key (e.g., 'soccer_epl')
            bookmakers: List of bookmakers to filter (default: ['betway'])
            markets: Markets to retrieve (default: ['h2h'])
            regions: Regions to include (default: ['uk', 'us'])
        
        Returns:
            Raw API response data
        """
        url = f"{self.base_url}/sports/{sport_key}/odds/"
        params = {
            'apiKey': self.api_key,
            'regions': ','.join(regions),
            'markets': ','.join(markets),
            'bookmakers': ','.join(bookmakers),
            'oddsFormat': 'decimal'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            requests_remaining = response.headers.get('x-requests-remaining')
            
            print(f"✅ Successfully extracted {sport_key}")
            print(f"   Matches found: {len(data)}")
            print(f"   Requests remaining: {requests_remaining}")
            
            return data
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print(f"❌ Authentication Error: Invalid API Key")
            elif response.status_code == 429:
                print(f"❌ Rate Limit Error: No requests remaining")
            else:
                print(f"❌ HTTP Error {response.status_code}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
            return None

    def transform_to_dataframe(self, raw_data):
        """
        Transform raw API data to structured DataFrame
        
        Args:
            raw_data: Raw API response data
        
        Returns:
            Pandas DataFrame with flattened data
        """
        records = []
        
        for game in raw_data:
            # For each game, look for Betway bookmaker
            for bookmaker in game.get('bookmakers', []):
                if bookmaker['key'] == 'betway':
                    # For each market in Betway
                    for market in bookmaker.get('markets', []):
                        # For each outcome (team/result)
                        for outcome in market.get('outcomes', []):
                            records.append({
                                'game_id': game['id'],
                                'sport_key': game['sport_key'],
                                'sport_title': game['sport_title'],
                                'commence_time': game['commence_time'],
                                'home_team': game['home_team'],
                                'away_team': game['away_team'],
                                'bookmaker': bookmaker['key'],
                                'market_type': market['key'],
                                'outcome_name': outcome['name'],
                                'odds': outcome['price'],
                                'extracted_at': datetime.utcnow().isoformat()
                            })
        
        if records:
            df = pd.DataFrame(records)
            print(f"✅ Transformed {len(records)} records to DataFrame")
            return df
        else:
            print(f"⚠️  No records found for transformation")
            return pd.DataFrame()

    def save_to_csv(self, df, filename='betway_odds'):
        """
        Save DataFrame to CSV file
        
        Args:
            df: Pandas DataFrame to save
            filename: Base filename (timestamp will be appended)
        
        Returns:
            Full filepath where file was saved
        """
        if df.empty:
            print("⚠️  Cannot save empty DataFrame")
            return None
        
        os.makedirs('data/raw', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = f"data/raw/{filename}_{timestamp}.csv"
        
        df.to_csv(filepath, index=False)
        print(f"✅ Saved {len(df)} records to {filepath}")
        
        return filepath


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Odds API Extractor - Testing")
    print("=" * 60)
    
    try:
        # Initialize extractor
        extractor = OddsAPIExtractor()
        print("\n✅ Extractor initialized successfully\n")
        
        # Get available sports
        print("Step 1: Fetching available sports...")
        print("-" * 60)
        sports = extractor.get_available_sports()
        
        if sports:
            # Find sports with data
            active_sports = [s for s in sports if s.get('active')]
            print(f"Active sports: {len(active_sports)}")
            
            # Test extraction with a specific sport
            print("\nStep 2: Testing extraction with soccer_epl...")
            print("-" * 60)
            test_sport = 'soccer_epl'
            raw_odds = extractor.extract_odds(test_sport)
            
            if raw_odds:
                # Transform data
                print("\nStep 3: Transforming data...")
                print("-" * 60)
                df = extractor.transform_to_dataframe(raw_odds)
                
                if not df.empty:
                    # Save to CSV
                    print("\nStep 4: Saving to CSV...")
                    print("-" * 60)
                    filepath = extractor.save_to_csv(df, 'betway_odds_test')
                    
                    # Display sample
                    print("\n📊 Sample Data:")
                    print(df.head())
                    print(f"\nDataFrame shape: {df.shape}")
                else:
                    print("⚠️  No Betway odds found for this sport")
            else:
                print("⚠️  Failed to extract odds")
    
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
