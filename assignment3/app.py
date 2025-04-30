import http
import http.client
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv
import time
from functools import lru_cache
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

# Store conversation history
conversation_history = []

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'

# Rate limiting setup
last_request_time = 0
min_request_interval = 12  # Alpha Vantage free tier allows 5 calls per minute
rate_limit_lock = threading.Lock()

@lru_cache(maxsize=100)
def get_stock_info(symbol):
    global last_request_time
    
    try:
        # Rate limiting
        with rate_limit_lock:
            current_time = time.time()
            time_since_last_request = current_time - last_request_time
            if time_since_last_request < min_request_interval:
                time.sleep(min_request_interval - time_since_last_request)
            last_request_time = time.time()
        
        # Try to get stock data with retries
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': ALPHA_VANTAGE_API_KEY
                }
                
                response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    return {
                        'symbol': symbol,
                        'price': float(quote['05. price']),
                        'change': float(quote['09. change']),
                        'change_percent': quote['10. change percent'].rstrip('%'),
                        'volume': int(quote['06. volume']),
                        'latest_trading_day': quote['07. latest trading day']
                    }
                else:
                    raise Exception("No quote data available")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise e
        
        return None
    except Exception as e:
        logging.error(f"Error fetching stock price for {symbol}: {e}")
        return None

def strip_agentic_capabilities(prompt):
    # Add instructions to strip agentic capabilities
    stripped_prompt = f"""
    You are a simple LLM that provides information. Do not act as an agent or make decisions.
    Simply provide the requested information based on the data provided.
    
    Original prompt: {prompt}
    
    Remember: You are not an agent. You are just providing information.
    """
    return stripped_prompt

@app.route('/track_stock', methods=['POST'])
def track_stock():
    data = request.json
    symbol = data.get('symbol')
    
    if not symbol:
        return jsonify({'error': 'No symbol provided'}), 400
    
    # Get stock price
    stock_info = get_stock_info(symbol)
    if stock_info is None:
        return jsonify({'error': 'Could not fetch stock info'}), 400
    
    # Create prompt for Gemini
    prompt = f"What is the current price of {symbol} stock and what does this price indicate about the company's performance?"
    
    # Add to conversation history
    conversation_history.append({
        'role': 'user',
        'content': prompt
    })
    
    # Strip agentic capabilities
    stripped_prompt = strip_agentic_capabilities(prompt)
    logging.info(f"Stripped prompt: {stripped_prompt}")
    # Get response from Gemini
    response = model.generate_content(stripped_prompt)
    logging.info(f"Response: {response}")
    # Add response to conversation history
    conversation_history.append({
        'role': 'assistant',
        'content': response.text
    })
    
    return jsonify({
        'price': stock_info['price'],
        'analysis': response.text
    })

@app.route('/')
def index():
    return "Working"

if __name__ == '__main__':
    app.run(debug=True) 