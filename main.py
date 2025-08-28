from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import create_tables, get_db_connection, insert_price, get_prices, get_latest_timestamp, get_daily_summary_prices, get_latest_price, DATABASE_NAME
from coingecko import get_market_chart_range
import datetime
import time
from typing import Optional

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def on_startup():
    create_tables()

# Helper to convert YYYY-MM-DD to timestamp
def to_timestamp(date_str: str, start_of_day=True):
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    if not start_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return int(time.mktime(dt.timetuple()))

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()

@app.post("/ingest")
def ingest_data():
    """
    Ingests data in 90-day chunks to maximize speed while retaining hourly granularity.
    This process is resumable and will pick up from the last ingested timestamp.
    """
    try:
        currencies = ["usd", "btc"]
        conn = get_db_connection()

        for currency in currencies:
            latest_ts = get_latest_timestamp(currency)
            start_date = datetime.date(2020, 2, 4) # HNS inception date
            if latest_ts:
                start_date = datetime.date.fromtimestamp(latest_ts)

            to_date = datetime.date.today()
            
            print(f"Starting ingestion for currency '{currency}' from {start_date} to {to_date}")

            current_date = start_date
            while current_date <= to_date:
                chunk_start_date = current_date
                chunk_end_date = current_date + datetime.timedelta(days=89)
                if chunk_end_date > to_date:
                    chunk_end_date = to_date

                print(f"Fetching data for chunk: {chunk_start_date} to {chunk_end_date}")
                
                chart_data = get_market_chart_range("handshake", currency, chunk_start_date, chunk_end_date + datetime.timedelta(days=1))

                processed_data = {}
                for p in chart_data['prices']:
                    ts = int(p[0] / 1000)
                    if not latest_ts or ts > latest_ts:
                        processed_data[ts] = {'price': p[1]}

                for mc in chart_data['market_caps']:
                    ts = int(mc[0] / 1000)
                    if ts in processed_data:
                        processed_data[ts]['market_cap'] = mc[1]

                for tv in chart_data['total_volumes']:
                    ts = int(tv[0] / 1000)
                    if ts in processed_data:
                        processed_data[ts]['total_volume'] = tv[1]

                for ts, data in processed_data.items():
                    insert_price(conn, ts, currency, data.get('price'), data.get('market_cap'), data.get('total_volume'))

                time.sleep(1.2) # Delay for safety
                current_date += datetime.timedelta(days=90)

        conn.close()
        return {"message": "Ingestion process completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prices")
def read_prices(
    from_date: Optional[str] = Query(None, alias="from", description="Start date (YYYY-MM-DD). Defaults to today."),
    to_date: Optional[str] = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    currency: Optional[str] = Query("usd", description="Currency (e.g., usd, btc)")
):
    """
    Returns stored HNS price data with powerful filtering and aggregation.
    - If 'from' is not provided, it defaults to today.
    - If 'to' is not provided or is the same as 'from', returns all granular entries for that single day.
    - If 'to' is provided and is different from 'from', returns a single, latest entry for each day in the range.
    """
    try:
        if from_date is None:
            from_date = datetime.date.today().strftime('%Y-%m-%d')

        if not to_date:
            to_date = from_date

        from_ts = to_timestamp(from_date)
        to_ts = to_timestamp(to_date, start_of_day=False)

        if from_date == to_date:
            prices = get_prices(from_timestamp=from_ts, to_timestamp=to_ts, currency=currency)
        else:
            prices = get_daily_summary_prices(from_timestamp=from_ts, to_timestamp=to_ts, currency=currency)
        
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price")
def get_current_price(
    request: Request,
    currency: Optional[str] = Query("usd", description="Currency (e.g., usd, btc)")
):
    """
    Returns the most recent price for a given currency.
    - If 'Accept' header is 'application/json', returns the full data object.
    - Otherwise, returns only the price as plain text.
    """
    try:
        latest = get_latest_price(currency)
        if not latest:
            raise HTTPException(status_code=404, detail="No price data found for this currency.")

        accept_header = request.headers.get('accept', '').lower()

        if 'application/json' in accept_header:
            return latest
        else:
            price_value = latest['price']
            formatted_price = f"{price_value:.18f}"
            return PlainTextResponse(content=formatted_price)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/database")
def download_database():
    """
    Downloads the SQLite database file.
    """
    return FileResponse(path=DATABASE_NAME, filename="prices.db", media_type='application/x-sqlite3')