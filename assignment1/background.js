// Function to check if a URL matches any blocked sites
function isBlocked(url) {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['blockedSites'], function(result) {
      const blockedSites = result.blockedSites || [];
      const hostname = new URL(url).hostname.toLowerCase();
      const isBlocked = blockedSites.some(site => hostname.includes(site));
      resolve(isBlocked);
    });
  });
}

// Listen for navigation events
chrome.webNavigation.onBeforeNavigate.addListener(async function(details) {
  if (details.frameId === 0) { // Only block main frame navigation
    const blocked = await isBlocked(details.url);
    if (blocked) {
      chrome.tabs.update(details.tabId, {
        url: chrome.runtime.getURL('blocked.html')
      });
    }
  }
});

// Listen for tab updates
chrome.tabs.onUpdated.addListener(async function(tabId, changeInfo, tab) {
  if (changeInfo.status === 'loading' && tab.url) {
    const blocked = await isBlocked(tab.url);
    if (blocked) {
      chrome.tabs.update(tabId, {
        url: chrome.runtime.getURL('blocked.html')
      });
    }
  }
}); 