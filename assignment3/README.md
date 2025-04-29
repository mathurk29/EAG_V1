# Stock Price Tracker Chrome Extension

A Chrome extension that tracks stock prices using Gemini AI for analysis.

## Setup Instructions

1. Clone this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
4. Start the Python backend:
   ```bash
   python app.py
   ```
5. Load the Chrome extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the directory containing the extension files

## Usage

1. Click the extension icon in Chrome
2. Enter a stock symbol (e.g., AAPL, GOOGL, MSFT)
3. Click "Track Price" to get the current price and AI analysis

## Features

- Real-time stock price tracking
- AI-powered analysis using Gemini
- Simple and intuitive interface
- Maintains conversation history for context

## Note

The extension uses Gemini AI with stripped-down agentic capabilities to provide information-only responses. It does not make decisions or take actions on behalf of the user.
