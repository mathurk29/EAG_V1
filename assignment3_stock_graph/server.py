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

@lru_cache()
def get_stock_news(stock_name: str, from_date: str, to_date: str):
    try:
        # Convert dates to Unix timestamps
        from_timestamp = int(datetime.strptime(from_date, '%Y-%m-%d').timestamp())
        to_timestamp = int(datetime.strptime(to_date, '%Y-%m-%d').timestamp())
        
        # Get company news from Finnhub
        news = finnhub_client.company_news(stock_name, _from=from_date, to=to_date)
        
        if not news:
            return []
            
        # Process and format news articles
        formatted_news = []
        for article in news:
            formatted_news.append({
                'title': article.get('headline', ''),
                'summary': article.get('summary', ''),
                'url': article.get('url', ''),
                'publishedAt': datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'source': article.get('source', ''),
                'category': article.get('category', '')
            })
        
        return formatted_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

def get_stock_price(stock_name: str, date: str):
    try:
        # Get daily data for the month containing the date
        start_date = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=5)
        end_date = datetime.strptime(date, '%Y-%m-%d') + timedelta(days=5)
        
        data, meta_data = ts.get_daily(symbol=stock_name, outputsize='full')
        
        # Filter data for the specific date
        target_date = pd.to_datetime(date)
        if target_date in data.index:
            return float(data.loc[target_date]['4. close'])
        return None
    except Exception as e:
        logging.error(f"Error fetching stock price: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stock price: {str(e)}")

def plot_graph(stock_name: str, news_dates: list, prices: list):
    plt.figure(figsize=(12, 6))
    plt.plot(news_dates, prices, marker='o', linestyle='-', color='blue')
    plt.title(f'{stock_name} Stock Price on News Dates')
    plt.xlabel('Date')
    plt.ylabel('Price ($)')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save plot to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
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
        start_date = end_date - timedelta(days=3)
        
        # Get news
        news = get_stock_news(
            request.stock_name,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Extract dates and get prices
        news_dates = []
        prices = []
        news_summaries = []
        
        for article in news:
            date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
            price = get_stock_price(request.stock_name, date)
            if price is not None:
                news_dates.append(date)
                prices.append(price)
                news_summaries.append({
                    'date': date,
                    'title': article['title'],
                    'summary': article['summary']
                })
        
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
                "prices": prices,
                "news": news_summaries
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 