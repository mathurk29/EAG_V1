# Stock News Analyzer Chrome Extension

This Chrome Extension analyzes stock prices in relation to news events using LLM (Language Learning Model) integration.

## Setup Instructions

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
Create a `.env` file in the root directory with:
```
GOOGLE_API_KEY=your_google_api_key_here
```

3. Start the FastAPI server:
```bash
python server.py
```

4. Load the Chrome Extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" in the top right
   - Click "Load unpacked" and select the `chrome_extension` directory

## Usage

1. Click the extension icon in your Chrome toolbar
2. Enter a stock symbol (e.g., AAPL, GOOGL, MSFT)
3. Click "Analyze Stock"
4. View the graph showing stock prices and related news events

## Features

- Fetches stock news and historical prices
- Generates a graph showing price movements with news event markers
- Displays news summaries with corresponding price changes
- Uses LLM to analyze the relationship between news and price movements

## Technical Details

The extension consists of:
- Chrome Extension (popup.html, popup.js, manifest.json)
- FastAPI server (server.py)
- LLM integration using Google's Gemini API

The system follows an iterative approach to analyze stock data:
1. Fetches news and price data
2. Processes the data through the LLM
3. Generates visualizations and insights
4. Presents the results in an interactive interface

## Requirements

- Python 3.7+
- Chrome browser
- Google API key

## API Rate Limits

- Google: 100 API calls per minute (free tier)

Please be mindful of these limits when using the extension. 