
import requests
import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://pro-api.coingecko.com/api/v3"

def get_market_chart_range(coin_id, vs_currency, from_date, to_date):
    """
    Get historical market data include price, market cap, and 24h volume (granularity auto)
    """
    from_timestamp = int(time.mktime(from_date.timetuple()))
    to_timestamp = int(time.mktime(to_date.timetuple()))
    
    url = f"{BASE_URL}/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": vs_currency,
        "from": from_timestamp,
        "to": to_timestamp,
        "x_cg_pro_api_key": API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_ohlc(coin_id, vs_currency, days):
    """
    Get historical OHLC data.
    """
    url = f"{BASE_URL}/coins/{coin_id}/ohlc"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "x_cg_pro_api_key": API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_daily_price(coin_id, vs_currency):
    """
    Get the current price of any cryptocurrency in any other supported currency that you need.
    """
    url = f"{BASE_URL}/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": vs_currency,
        "x_cg_pro_api_key": API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()[coin_id][vs_currency]
