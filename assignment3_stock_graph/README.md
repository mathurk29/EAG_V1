
# [DEMO](https://youtu.be/m4wwKMi6kPc)


# Stock Analysis and Visualization System

This system provides a comprehensive solution for stock analysis, visualization, and email notifications through a Chrome extension interface. It combines multiple data sources and APIs to deliver real-time stock information and insights.

## SYSTEM_PROMPT

```
You are a stock market agent who solves problem in iteration.

Respond in EXACTLY ONE of these formats:

1. FUNCTION_CALL: python_function_name|jsonified_parameter_string
2. TASK_COMPLETE: <task_complete_message>
3. INSUFFICIENT_TOOLS: <advise what additional tools are required>


You have the following tools at hand. You are supposed to complete the task only using the following tools.

where python_function_name is one of the following:
1. get_stock_news(stock_name,from_date,to_date):return news
2. get_stock_price(stock_name,from_date,to_date): return list of prices for the given stock name and date range in chronological ascending order
3. send_email(recipient_email,stock_name,body): return True if email is sent successfully, else return False


For example: if you are responding for getting stock news for stock named Ola for last 3 days, then you should return:
FUNCTION_CALL: get_stock_news|{"stock_name":"OLA","from_date":"2024-04-28","to_date":"2024-05-01"}

DO NOT include multiple responses. Give ONE response at a time.
DO NOT GIVE EXPLANATION OR REASONING. JUST RETURN THE RESPONSE IN THE SPECIFIED FORMAT.
DO NOT BREACH THE CONTRACT OF RESPONSE FORMAT!!!!!
```

## QUERY_PROMPT


```
Find the news about ${stockName} and link it with its price changes from ${fromDate} to ${toDate} then see how the stock moved on those dates. Keep the analysis for a particular day within 50 words. Send the analysis to XXXXX@gmail.com
```


## System Architecture

The system consists of three main components:

1. **Backend Server (FastAPI)**
   - Handles API requests from the Chrome extension
   - Integrates with multiple data sources (Alpha Vantage, Finnhub)
   - Manages data caching using Redis
   - Provides email notification functionality

2. **Chrome Extension**
   - User interface for interacting with the system
   - Real-time stock data visualization
   - News aggregation and display
   - Email notification interface

3. **Data Storage (Redis)**
   - Caches stock prices, news, and plot data
   - Optimizes API calls and improves response times
   - Maintains historical data for quick retrieval

## Features

- **Stock Price Analysis**
  - Historical price data retrieval
  - Interactive price charts
  - Technical analysis visualization

- **News Integration**
  - Company news aggregation
  - Date-based news filtering
  - News impact analysis

- **Email Notifications**
  - Customizable email alerts
  - Stock analysis reports
  - Visual charts in emails

## Setup Instructions

1. **Environment Setup**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv add -r requirements.txt
   ```

2. **Environment Setup**
   Create a `.env` file with the following variables:
   ```
   ALPHA_VANTAGE_KEY=your_alpha_vantage_key
   FINNHUB_KEY=your_finnhub_key
   GMAIL_USER=your_gmail_address
   REDIS_URL=redis://127.0.0.1:6379
   ```
3. To send emails via Gmail API using Python and OAuth 2.0, follow these steps: 

   a. Go to: https://console.cloud.google.com/

   b. Create a new project (or use existing one).

   c. Enable Gmail API from “APIs & Services > Library”.

   d. Go to “Credentials” → Click “Create Credentials” → Choose OAuth client ID

   e. Application Type: Desktop App

   f. Download the client_secret.json file.

   To bypass “App not verified” screen

   a. Go to OAuth Consent Screen

   b. Choose “External” user type

   c. Fill in required details (App name, email, etc.)

   d. Add https://www.googleapis.com/auth/gmail.send in Scopes

   e. Add your Gmail address in Test Users

   Now when your project executes the OAuth connection - and Google gives “App not verified” screen:

   a. Click "Advanced"
   
   b. "Go to your_project_name (unsafe)"

   c. continue login and grant permission.




4. **Redis Setup**
   - Install Redis on your system
   - Start Redis server
   - The system will automatically connect to Redis on startup

5. **Chrome Extension Setup**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `chrome_extension` directory

6. **Start the Server**
   ```bash
   python server.py
   ```

## API Endpoints

The server provides the following endpoints:

- `POST /call_function`: Main endpoint for all function calls
  - Parameters:
    - `func_name`: Name of the function to call
    - `params`: Dictionary of parameters for the function

## Available Functions

1. `get_stock_news(stock_name, from_date, to_date)`
   - Retrieves news for a specific stock within a date range
   - Returns filtered news with date, title, and summary

2. `get_stock_price(stock_name, from_date, to_date)`
   - Fetches historical stock prices
   - Returns list of closing prices

3. `plot_graph(stock_name, from_date, to_date)`
   - Generates interactive stock price charts
   - Returns plot data in JSON format

4. `send_email(recipient_email, stock_name, body)`
   - Sends email notifications with stock analysis
   - Includes visual charts and analysis

## Data Storage

The system uses Redis for efficient data caching:

1. **NewsStorage**
   - Stores news data by stock and date
   - Optimizes news retrieval and filtering

2. **StockPriceStorage**
   - Caches historical price data
   - Reduces API calls to Alpha Vantage

3. **PlotStorage**
   - Stores generated plot data
   - Improves response times for repeated requests

## Dependencies

- FastAPI
- Redis
- Alpha Vantage API
- Finnhub API
- Plotly
- Pandas
- Python-dotenv
- YFinance

## Security Considerations

- API keys are stored in environment variables
- CORS is configured to only allow Chrome extension requests
- Gmail authentication uses app-specific passwords
- Redis connection is secured with proper error handling

## Error Handling

The system includes comprehensive error handling for:
- API failures
- Redis connection issues
- Invalid data formats
- Missing environment variables
- Network connectivity problems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 