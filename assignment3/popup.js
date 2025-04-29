document.addEventListener('DOMContentLoaded', function() {
  const trackButton = document.getElementById('trackButton');
  const stockSymbol = document.getElementById('stockSymbol');
  const resultDiv = document.getElementById('result');

  trackButton.addEventListener('click', async function() {
    const symbol = stockSymbol.value.trim().toUpperCase();
    if (!symbol) {
      resultDiv.textContent = 'Please enter a stock symbol';
      return;
    }

    try {
      resultDiv.textContent = 'Fetching stock data...';
      
      // Send message to background script
      chrome.runtime.sendMessage(
        { action: 'trackStock', symbol: symbol },
        function(response) {
          if (response.error) {
            resultDiv.textContent = `Error: ${response.error}`;
          } else {
            resultDiv.textContent = `Current price of ${symbol}: $${response.price}`;
          }
        }
      );
    } catch (error) {
      resultDiv.textContent = `Error: ${error.message}`;
    }
  });
}); 