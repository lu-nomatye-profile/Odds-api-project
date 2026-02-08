"""
Simple test script to verify API connection and configuration.
Run this to ensure everything is set up correctly before running the full pipeline.
"""

import requests
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_api_key():
    """Test if API key is properly configured"""
    print("\n" + "=" * 60)
    print("TEST 1: API Key Configuration")
    print("=" * 60)
    
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        print("❌ FAILED: ODDS_API_KEY not found in environment")
        print("   Action: Check your .env file or set environment variable")
        return False
    
    if api_key == 'your_api_key_here':
        print("❌ FAILED: ODDS_API_KEY is still set to default value")
        print("   Action: Replace with your actual API key from https://the-odds-api.com/")
        return False
    
    print(f"✅ PASSED: API Key found ({api_key[:5]}***{api_key[-3:]})")
    return True


def test_api_connection():
    """Test if we can actually connect to The Odds API"""
    print("\n" + "=" * 60)
    print("TEST 2: API Connection")
    print("=" * 60)
    
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        print("❌ SKIPPED: No API key available")
        return False
    
    try:
        url = "https://api.the-odds-api.com/v4/sports/"
        params = {'apiKey': api_key}
        
        print(f"Connecting to: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            requests_remaining = response.headers.get('x-requests-remaining', 'Unknown')
            
            print(f"✅ PASSED: Successfully connected to The Odds API")
            print(f"   Status Code: {response.status_code}")
            print(f"   Sports Available: {len(data)}")
            print(f"   Requests Remaining This Month: {requests_remaining}")
            
            return True
        
        elif response.status_code == 401:
            print(f"❌ FAILED: Authentication Error (401)")
            print(f"   Your API key appears to be invalid")
            print(f"   Action: Verify key at https://the-odds-api.com/account/")
            return False
        
        elif response.status_code == 429:
            print(f"❌ FAILED: Rate Limited (429)")
            print(f"   You've exceeded your monthly request limit")
            print(f"   Action: Wait until next month or upgrade your plan")
            return False
        
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED: Cannot connect to API")
        print(f"   Action: Check your internet connection")
        return False
    
    except requests.exceptions.Timeout:
        print(f"❌ FAILED: Request timeout")
        print(f"   Action: API is slow or unreachable")
        return False
    
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_betway_odds():
    """Test if we can get Betway odds for a specific sport"""
    print("\n" + "=" * 60)
    print("TEST 3: Betway Odds Availability")
    print("=" * 60)
    
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        print("❌ SKIPPED: No API key available")
        return False
    
    try:
        sport_key = 'soccer_epl'
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        params = {
            'apiKey': api_key,
            'regions': 'uk,us',
            'markets': 'h2h,spreads,totals',
            'bookmakers': 'betway',
            'oddsFormat': 'decimal'
        }
        
        print(f"Fetching odds for: {sport_key} (Betway only)")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if len(data) > 0:
                print(f"✅ PASSED: Found Betway odds for {sport_key}")
                print(f"   Matches available: {len(data)}")
                
                # Check first match
                match = data[0]
                print(f"   Sample match: {match['home_team']} vs {match['away_team']}")
                
                # Dump data structure (first match)
                print(f"   Match ID: {match['id']}")
                print(f"   Commence: {match['commence_time']}")
                
                return True
            else:
                print(f"⚠️  WARNING: No Betway odds found for {sport_key}")
                print(f"   Betway may not be offering odds for this sport right now")
                print(f"   Try: soccer_uefa_champs_league, basketball_nba, etc.")
                return True  # Still pass - API is working
        
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_python_dependencies():
    """Test if all required Python packages are installed"""
    print("\n" + "=" * 60)
    print("TEST 4: Python Dependencies")
    print("=" * 60)
    
    required_packages = {
        'requests': 'API calls',
        'pandas': 'Data processing',
        'dotenv': 'Environment variables',
        'airflow': 'Orchestration',
        'databricks': 'Databricks connection',
    }
    
    all_installed = True
    
    for package, purpose in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package:<20} - {purpose}")
        except ImportError:
            print(f"❌ {package:<20} - {purpose} [NOT INSTALLED]")
            all_installed = False
    
    if not all_installed:
        print("\nTo install missing packages, run:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Run all tests and report results"""
    print("\n" + "🧪 ODDS API PROJECT - CONFIGURATION TEST SUITE" + "\n")
    
    results = {
        "API Key Configuration": test_api_key(),
        "API Connection": test_api_connection(),
        "Betway Odds": test_betway_odds(),
        "Python Dependencies": test_python_dependencies(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to go!")
        print("\nNext steps:")
        print("  1. cd docker")
        print("  2. docker-compose up -d")
        print("  3. Open http://localhost:8080 in your browser")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above and try again.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
