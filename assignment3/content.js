// Content script for Stock Price Tracker
// This script runs in the context of web pages

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageInfo') {
    // You can add functionality here to interact with the webpage if needed
    sendResponse({ status: 'success' });
  }
  return true;
}); 