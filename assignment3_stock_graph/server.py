from functools import lru_cache
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from alpha_vantage.timeseries import TimeSeries
from finnhub import Client as FinnhubClient
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import io
import base64
import os
from dotenv import load_dotenv
import yfinance as yf
from typing import List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import redis
import json
import pickle
import sys

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

# Initialize API clients and Redis
alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
finnhub_key = os.getenv('FINNHUB_KEY')
gmail_user = os.getenv('GMAIL_USER')
gmail_password = os.getenv('GMAIL_APP_PASSWORD')
redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')

if not all([alpha_vantage_key, finnhub_key, gmail_user, gmail_password]):
    raise ValueError("Please set all required environment variables in .env file")

def check_redis_connection():
    """Check if Redis server is up and running"""
    try:
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        print("Connected to Redis successfully")
        return redis_client
    except redis.ConnectionError as e:
        logging.error(f"Failed to connect to Redis: {str(e)}")
        print("Error: Redis server is not running. Please start Redis server and try again.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error connecting to Redis: {str(e)}")
        print("Error: Unexpected error connecting to Redis server.")
        sys.exit(1)

# Initialize Redis with connection check
redis_client = check_redis_connection()

ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
finnhub_client = FinnhubClient(api_key=finnhub_key)

class NewsStorage:
    """Redis-backed storage for stock news data with day-wise storage"""
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "news:"
    
    def _get_key(self, stock_name: str, date: str) -> str:
        """Generate a unique key for the news data for a specific date"""
        return f"{self.prefix}{stock_name}:{date}"
    
    def _get_date_range_keys(self, stock_name: str, from_date: str, to_date: str) -> List[str]:
        """Generate keys for all dates in the range"""
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        date_keys = []
        
        current_dt = from_dt
        while current_dt <= to_dt:
            date_keys.append(self._get_key(stock_name, current_dt.strftime("%Y-%m-%d")))
            current_dt += timedelta(days=1)
        
        return date_keys
    
    def store_news(self, stock_name: str, from_date: str, to_date: str, news: List[Dict[str, Any]]):
        """Store news data in Redis, organized by date"""
        # Group news by date
        news_by_date = {}
        for item in news:
            date = item["date"]
            if date not in news_by_date:
                news_by_date[date] = []
            news_by_date[date].append(item)
        
        # Store each day's news separately
        for date, day_news in news_by_date.items():
            key = self._get_key(stock_name, date)
            self.redis.set(key, json.dumps(day_news))
    
    def get_news(self, stock_name: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """Retrieve news data from Redis for a date range"""
        # Get all keys in the date range
        keys = self._get_date_range_keys(stock_name, from_date, to_date)
        
        # Use pipeline to get all data in one network round trip
        pipeline = self.redis.pipeline()
        for key in keys:
            pipeline.get(key)
        results = pipeline.execute()
        
        # Combine all news items
        all_news = []
        for data in results:
            if data:
                all_news.extend(json.loads(data))
        
        return all_news
    
    def get_news_for_date(self, stock_name: str, date: str) -> List[Dict[str, Any]]:
        """Retrieve news data for a specific date"""
        key = self._get_key(stock_name, date)
        data = self.redis.get(key)
        return json.loads(data) if data else []
    
    def has_news_for_date(self, stock_name: str, date: str) -> bool:
        """Check if we have news data for a specific date"""
        key = self._get_key(stock_name, date)
        return bool(self.redis.exists(key))
    
    def get_missing_dates(self, stock_name: str, from_date: str, to_date: str) -> List[str]:
        """Get list of dates in range that don't have news data"""
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        missing_dates = []
        
        current_dt = from_dt
        while current_dt <= to_dt:
            current_date = current_dt.strftime("%Y-%m-%d")
            if not self.has_news_for_date(stock_name, current_date):
                missing_dates.append(current_date)
            current_dt += timedelta(days=1)
        
        return missing_dates

class StockPriceStorage:
    """Redis-backed storage for stock price data"""
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "prices:"
    
    def _get_key(self, stock_name: str, from_date: str, to_date: str) -> str:
        """Generate a unique key for the stock price data"""
        return f"{self.prefix}{stock_name}_{from_date}_{to_date}"
    
    def store_prices(self, stock_name: str, from_date: str, to_date: str, data: pd.DataFrame):
        """Store stock price data in Redis"""
        key = self._get_key(stock_name, from_date, to_date)
        self.redis.set(key, pickle.dumps(data))
    
    def get_prices(self, stock_name: str, from_date: str, to_date: str) -> pd.DataFrame:
        """Retrieve stock price data from Redis"""
        key = self._get_key(stock_name, from_date, to_date)
        data = self.redis.get(key)
        return pickle.loads(data) if data else None

class PlotStorage:
    """Redis-backed storage for stock plot data"""
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "plot:"
    
    def store_plot(self, stock_name: str, plot_data: Dict[str, Any]):
        """Store plot data in Redis"""
        key = f"{self.prefix}{stock_name}"
        self.redis.set(key, json.dumps(plot_data))
    
    def get_plot(self, stock_name: str) -> Dict[str, Any]:
        """Retrieve plot data from Redis"""
        key = f"{self.prefix}{stock_name}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

# Initialize storage instances with Redis client
news_storage = NewsStorage(redis_client)
price_storage = StockPriceStorage(redis_client)
plot_storage = PlotStorage(redis_client)

class StockRequest(BaseModel):
    stock_name: str
    from_date: str
    to_date: str

class FunctionCall(BaseModel):
    func_name: str
    params: Dict[str, Any]

def get_stock_news(stock_name: str, from_date: str, to_date: str) -> str:
    """Get news for a stock using Finnhub and store it in Redis"""
    try:
        # Check which dates we already have news for
        missing_dates = news_storage.get_missing_dates(stock_name, from_date, to_date)
        
        if not missing_dates:
            # We already have all the news data
            return news_storage.get_news(stock_name, from_date, to_date)
        
        # Convert dates to timestamps for API call
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
        
        # Store news in Redis, organized by date
        news_storage.store_news(stock_name, from_date, to_date, filtered_news)
        
        # Return combined news for the requested date range
        return news_storage.get_news(stock_name, from_date, to_date)
    except Exception as e:
        logging.error(f"Error getting stock news from Finnhub: {str(e)}")
        return False

def get_stock_price(stock_name: str, from_date: str, to_date: str) -> List[float]:
    """Get historical stock prices for a date range using Alpha Vantage"""
    try:
        # Check if data is in storage
        stored_data = price_storage.get_prices(stock_name, from_date, to_date)
        if stored_data is not None:
            return [float(price) for price in stored_data['4. close']]
        
        # Get daily data from Alpha Vantage
        data, meta_data = ts.get_daily(symbol=stock_name, outputsize='full')
        
        # Convert date strings to datetime
        from_date_dt = pd.to_datetime(from_date)
        to_date_dt = pd.to_datetime(to_date)
        
        # Filter data for the date range
        mask = (data.index >= from_date_dt) & (data.index <= to_date_dt)
        filtered_data = data.loc[mask]
        
        if filtered_data.empty:
            return []
        
        # Store the filtered data
        price_storage.store_prices(stock_name, from_date, to_date, filtered_data)
            
        # Return list of closing prices
        return [float(price) for price in filtered_data['4. close']]
    except Exception as e:
        logging.error(f"Error getting stock prices from Alpha Vantage: {str(e)}")
        return []

from gmail_client import get_gmail_service

def send_email(recipient_email: str, stock_name: str, body: str) -> bool:
    """Send email with stock plot attachment"""
    try:
        service = get_gmail_service()
        message = MIMEMultipart()
        message['from'] = os.getenv('GMAIL_USER')
        message['to'] = recipient_email
        message['Subject'] = f"Stock Analysis Graph for {stock_name}"

        # Email body
        message.attach(MIMEText(body, 'plain'))

        # Attach the plot
        stored_plot = plot_storage.get_plot(stock_name)
        if stored_plot is None:
            logging.info(f"No plot data found for stock {stock_name}, mail will be sent without plot attachment")
            
        # Attach the plot
        if stored_plot:
            image_data = base64.b64decode(stored_plot)
            image = MIMEImage(image_data)
            image.add_header('Content-Disposition', 'attachment', filename=f'{stock_name}_analysis.png')
            message.attach(image)

        # Send email
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {'raw': raw}
        send_message = service.users().messages().send(userId="me", body=message_body).execute()
        print(f'Email sent! Message Id: {send_message["id"]}')
        return True
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False

def plot_graph(stock_name: str, from_date: str, to_date: str) -> Dict[str, Any]:
    """Create a plot of stock prices with news markers using Plotly"""
    # Get prices and dates from storage or API
    prices = get_stock_price(stock_name, from_date, to_date)
    
    # Get the stored data
    stored_data = price_storage.get_prices(stock_name, from_date, to_date)
    if stored_data is None:
        return {
            "message": "No data available for the specified date range, advise you to call get_stock_price function first"
        }
    
    # Convert index to datetime and sort
    stored_data.index = pd.to_datetime(stored_data.index)
    stored_data = stored_data.sort_index()
    
    # Get the actual dates where we have price data
    dates = stored_data.index.strftime('%Y-%m-%d').tolist()
    prices = stored_data['4. close'].tolist()
    
    # Get news from storage
    news = news_storage.get_news(stock_name, from_date, to_date)
    
    # Create the main price line
    fig = go.Figure()
    
    # Add the main price line
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines+markers',
        name='Stock Price',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Add news markers and annotations
    for i, news_item in enumerate(news):
        date = news_item["date"]
        if date in dates:
            idx = dates.index(date)
            price = prices[idx]
            
            # Add news marker
            fig.add_trace(go.Scatter(
                x=[date],
                y=[price],
                mode='markers',
                name=news_item["title"][:30],
                marker=dict(
                    size=12,
                    color='red',
                    symbol='star',
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                showlegend=False
            ))
            
            # Add news annotation
            fig.add_annotation(
                x=date,
                y=price,
                text=news_item["title"][:30] + "...",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#636363",
                ax=0,
                ay=-40 if i % 2 == 0 else 40,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
                borderpad=4,
                font=dict(size=10)
            )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'Stock Price with News Events - {stock_name}',
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='Date',
            tickangle=45,
            gridcolor='lightgrey',
            showgrid=True
        ),
        yaxis=dict(
            title='Price',
            gridcolor='lightgrey',
            showgrid=True
        ),
        plot_bgcolor='white',
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Rockwell"
        ),
        margin=dict(t=100, b=100)
    )
    
    # Add range slider
    fig.update_xaxes(rangeslider_visible=True)
    
    # Convert plot to base64 string
    buf = io.BytesIO()
    pio.write_image(fig, buf, format='png', width=1200, height=800, scale=2)
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.getvalue()).decode()
    
    response = {
        "message": "Plot saved successfully in memory."
    }

    # Store the plot data
    plot_storage.store_plot(stock_name, plot_base64)
    return response


def function_caller(func_name: str, params: Dict[str, Any]) -> Any:
    """Call the appropriate function based on the function name"""
    function_map = {
        "get_stock_news": get_stock_news,
        "get_stock_price": get_stock_price,
        "plot_graph": plot_graph,
        "send_email": send_email
    }
    
    if func_name in function_map:
        return function_map[func_name](**params)
    else:
        raise ValueError(f"Function {func_name} not found")

@app.post("/call_function")
async def call_function(request: FunctionCall):
    try:    
        result = function_caller(request.func_name, request.params)
        if result is None or result == "" or result == []:
            raise HTTPException(status_code=500, detail=f"No result from function {request.func_name}")
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 