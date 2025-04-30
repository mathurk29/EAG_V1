# Stock News Analyzer Chrome Extension

This Chrome Extension analyzes stock prices based on news articles and displays the correlation between news events and stock price movements.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory and add your News API key:
```
NEWS_API_KEY=your_news_api_key_here
```

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
4. View the analysis results and graph showing stock price movements on news dates

## Features

- Fetches news articles for the specified stock
- Retrieves historical stock prices
- Generates a graph showing price movements on news dates
- Displays analysis results in the extension popup

## Requirements

- Python 3.7+
- Chrome browser
- News API key (get one from https://newsapi.org/) 