# Stock News Analyzer Chrome Extension

This Chrome Extension analyzes stock prices based on news articles and displays the correlation between news events and stock price movements.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory and add your API keys:
```
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here
FINNHUB_KEY=your_finnhub_key_here
```

You can get your API keys from:
- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- Finnhub: https://finnhub.io/register

3. Start the FastAPI server:
```bash
python server.py
```

4. Load the Chrome Extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" in the top right
   - Click "Load unpacked" and select the directory containing the extension files

## Usage

1. Click the extension icon in Chrome
2. Enter a stock symbol (e.g., AAPL, GOOGL, MSFT)
3. Click "Analyze Stock"
4. View the analysis results including:
   - A graph showing stock price movements on news dates
   - News articles with their corresponding stock prices
   - Detailed summaries of each news event

## Features

- Fetches real-time stock prices using Alpha Vantage API
- Retrieves company news using Finnhub API
- Generates an interactive graph showing price movements on news dates
- Displays detailed news analysis with price correlations
- Modern and responsive UI design

## Requirements

- Python 3.7+
- Chrome browser
- Alpha Vantage API key
- Finnhub API key

## API Rate Limits

- Alpha Vantage: 5 API calls per minute and 500 calls per day (free tier)
- Finnhub: 60 API calls per minute (free tier)

Please be mindful of these limits when using the extension. 