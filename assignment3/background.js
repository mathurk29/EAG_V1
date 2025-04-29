chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'trackStock') {
    // Make API call to our Python backend
    fetch('http://localhost:5000/track_stock', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol: request.symbol })
    })
    .then(response => response.json())
    .then(data => {
      sendResponse(data);
    })
    .catch(error => {
      sendResponse({ error: error.message });
    });
    return true; // Required for async sendResponse
  }
}); 