from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import yfinance as yf
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Store conversation history
conversation_history = []

def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        return stock.info.get('regularMarketPrice', None)
    except Exception as e:
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
    price = get_stock_price(symbol)
    if price is None:
        return jsonify({'error': 'Could not fetch stock price'}), 400
    
    # Create prompt for Gemini
    prompt = f"What is the current price of {symbol} stock and what does this price indicate about the company's performance?"
    
    # Add to conversation history
    conversation_history.append({
        'role': 'user',
        'content': prompt
    })
    
    # Strip agentic capabilities
    stripped_prompt = strip_agentic_capabilities(prompt)
    
    # Get response from Gemini
    response = model.generate_content(stripped_prompt)
    
    # Add response to conversation history
    conversation_history.append({
        'role': 'assistant',
        'content': response.text
    })
    
    return jsonify({
        'price': price,
        'analysis': response.text
    })

if __name__ == '__main__':
    app.run(debug=True) 