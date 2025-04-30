from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os
from dotenv import load_dotenv

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

# Initialize News API client
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

class StockRequest(BaseModel):
    stock_name: str

def get_stock_news(stock_name: str, from_date: str, to_date: str):
    try:
        news = newsapi.get_everything(
            q=stock_name,
            from_param=from_date,
            to=to_date,
            language='en',
            sort_by='publishedAt'
        )
        return news['articles']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_stock_price(stock_name: str, date: str):
    try:
        stock = yf.Ticker(stock_name)
        hist = stock.history(start=date, end=date)
        if hist.empty:
            return None
        return hist['Close'].iloc[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def plot_graph(stock_name: str, news_dates: list, prices: list):
    plt.figure(figsize=(12, 6))
    plt.plot(news_dates, prices, marker='o')
    plt.title(f'{stock_name} Stock Price on News Dates')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save plot to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Convert to base64
    img_str = base64.b64encode(buf.read()).decode()
    return img_str

@app.post("/analyze")
async def analyze_stock(request: StockRequest):
    try:
        # Get dates for last month
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Get news
        news = get_stock_news(
            request.stock_name,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Extract dates and get prices
        news_dates = []
        prices = []
        
        for article in news:
            date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
            price = get_stock_price(request.stock_name, date)
            if price is not None:
                news_dates.append(date)
                prices.append(price)
        
        if not news_dates:
            return {
                "status": "error",
                "message": "No valid news dates found for analysis"
            }
        
        # Generate plot
        plot_data = plot_graph(request.stock_name, news_dates, prices)
        
        return {
            "status": "success",
            "message": "Analysis complete",
            "plot": plot_data,
            "data": {
                "dates": news_dates,
                "prices": prices
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 