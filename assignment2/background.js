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

// Function to check if a URL is a Chrome internal page
function isChromeInternalPage(url) {
  const chromeInternalProtocols = [
    'chrome://',
    'chrome-extension://',
    'about:',
    'chrome-search://',
    'devtools://'
  ];
  
  return chromeInternalProtocols.some(protocol => url.startsWith(protocol));
}

// Function to check with Gemini if a site is distracting
async function checkWithGemini(site) {
  try {
    const result = await chrome.storage.sync.get(['apiKey']);
    if (!result.apiKey) {
      return false;
    }

    const response = await fetch(`https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key=${result.apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: `Is ${site} a distracting website that should be blocked to maintain focus? Answer with only 'yes' or 'no'.`
          }]
        }]
      })
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const data = await response.json();
    const answer = data.candidates[0].content.parts[0].text.toLowerCase().trim();
    return answer === 'yes';
  } catch (error) {
    console.error('Error checking site with Gemini:', error);
    return false;
  }
}

// Function to check if a URL should be blocked
async function shouldBlock(url) {
  // Don't block Chrome internal pages
  if (isChromeInternalPage(url)) {
    return false;
  }

  const hostname = new URL(url).hostname.toLowerCase();
  
  // First check if it's in the blocked list
  const isInBlockedList = await isBlocked(url);
  if (isInBlockedList) {
    return true;
  }

  // If not in blocked list, check with Gemini
  return await checkWithGemini(hostname);
}

// Listen for navigation events
chrome.webNavigation.onBeforeNavigate.addListener(async function(details) {
  if (details.frameId === 0) { // Only block main frame navigation
    const blocked = await shouldBlock(details.url);
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
    const blocked = await shouldBlock(tab.url);
    if (blocked) {
      chrome.tabs.update(tabId, {
        url: chrome.runtime.getURL('blocked.html')
      });
    }
  }
});