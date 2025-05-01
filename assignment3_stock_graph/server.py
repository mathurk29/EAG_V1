from functools import lru_cache
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from alpha_vantage.timeseries import TimeSeries
from finnhub import Client as FinnhubClient
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os
from dotenv import load_dotenv
import yfinance as yf
from typing import List, Dict, Any

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API clients
alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
finnhub_key = os.getenv('FINNHUB_KEY')

if not alpha_vantage_key or not finnhub_key:
    raise ValueError("Please set ALPHA_VANTAGE_KEY and FINNHUB_KEY in .env file")

ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
finnhub_client = FinnhubClient(api_key=finnhub_key)

class StockRequest(BaseModel):
    stock_name: str
    from_date: str
    to_date: str

class FunctionCall(BaseModel):
    func_name: str
    params: Dict[str, Any]

@lru_cache(maxsize=1000)
def get_stock_news(stock_name: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """Get news for a stock using Finnhub"""
    try:
        # Convert dates to timestamps
        from_timestamp = int(datetime.strptime(from_date, "%Y-%m-%d").timestamp())
        to_timestamp = int(datetime.strptime(to_date, "%Y-%m-%d").timestamp())
        
        # Get company news from Finnhub
        news = finnhub_client.company_news(stock_name, _from=from_date, to=to_date)
        
        filtered_news = [
            {
                "date": datetime.fromtimestamp(n["datetime"]).strftime("%Y-%m-%d"),
                "title": n["headline"],
                "summary": n.get("summary", "No summary available")
            }
            for n in news
            if from_timestamp <= n["datetime"] <= to_timestamp
        ]
        return filtered_news
    except Exception as e:
        logging.error(f"Error getting stock news from Finnhub: {str(e)}")
        return []

def get_stock_price(stock_name: str, date: str) -> float:
    """Get historical stock price for a specific date using Alpha Vantage"""
    try:
        # Get daily data from Alpha Vantage
        data, meta_data = ts.get_daily(symbol=stock_name, outputsize='full')
        
        # Convert date string to datetime
        target_date = pd.to_datetime(date)
        
        # Find the closest date in the data
        if target_date in data.index:
            return float(data.loc[target_date]['4. close'])
        else:
            # If exact date not found, get the closest previous date
            available_dates = data.index[data.index <= target_date]
            if len(available_dates) > 0:
                closest_date = available_dates[-1]
                return float(data.loc[closest_date]['4. close'])
            return None
    except Exception as e:
        logging.error(f"Error getting stock price from Alpha Vantage: {str(e)}")
        return None

def plot_graph(prices: List[float], dates: List[str], news: List[Dict[str, Any]]) -> str:
    """Create a plot of stock prices with news markers"""
    plt.figure(figsize=(12, 6))
    plt.plot(dates, prices, label='Stock Price', marker='o')
    
    # Add news markers
    for news_item in news:
        date = news_item["date"]
        if date in dates:
            idx = dates.index(date)
            price = prices[idx]
            plt.scatter(date, price, color='red', s=100, alpha=0.5)
            plt.annotate(news_item["title"][:30] + "...", 
                        (date, price),
                        xytext=(10, 10),
                        textcoords='offset points')
    
    plt.title('Stock Price with News Events')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # Convert plot to base64 string
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode()

def function_caller(func_name: str, params: Dict[str, Any]) -> Any:
    """Call the appropriate function based on the function name"""
    function_map = {
        "get_stock_news": get_stock_news,
        "get_stock_price": get_stock_price,
        "plot_graph": plot_graph
    }
    
    if func_name in function_map:
        return function_map[func_name](**params)
    else:
        raise ValueError(f"Function {func_name} not found")

@app.post("/call_function")
async def call_function(request: FunctionCall):
    try:
        result = function_caller(request.func_name, request.params)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 