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
import google.generativeai as genai
import ast
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

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Please set GOOGLE_API_KEY environment variable")

genai.configure(api_key=GOOGLE_API_KEY)
client = genai.GenerativeModel('gemini-pro')

# System prompt for the LLM
SYSTEM_PROMPT = """
You are a stock market agent who solves problem in iteration.

Respond with EXACTLY ONE of these formats:

1. FUNCTION_CALL: python_function_name|input

You have the following tools at hand. You are supposed to complete the task only using the following tools. If these tools are not sufficient - advise what additional tools are required.

where python_function_name is one of the following:
1. get_stock_news(stock_name,from_date,to_date)
2. get_stock_price(date)
3. plot_graph

Task: Find the news about a particular stock and link it with its price changes (e.g. search news about Ola in the last 1 month and news date, then see how the stock moved on those dates, and then link this data)

DO NOT include multiple responses. Give ONE response at a time.
"""

class StockRequest(BaseModel):
    stock_name: str
    from_date: str
    to_date: str

class FunctionCall(BaseModel):
    func_name: str
    params: Dict[str, Any]

def get_stock_news(stock_name: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """Get news for a stock using yfinance"""
    stock = yf.Ticker(stock_name)
    news = stock.news
    filtered_news = [
        {
            "date": datetime.fromtimestamp(n["providerPublishTime"]).strftime("%Y-%m-%d"),
            "title": n["title"],
            "summary": n.get("summary", "No summary available")
        }
        for n in news
        if from_date <= datetime.fromtimestamp(n["providerPublishTime"]).strftime("%Y-%m-%d") <= to_date
    ]
    return filtered_news

def get_stock_price(stock_name: str, date: str) -> float:
    """Get historical stock price for a specific date"""
    stock = yf.Ticker(stock_name)
    hist = stock.history(start=date, end=date)
    if not hist.empty:
        return float(hist['Close'].iloc[0])
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