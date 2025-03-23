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

// Function to get cached Gemini response
function getCachedGeminiResponse(site) {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['geminiResponses'], function(result) {
      const responses = result.geminiResponses || {};
      resolve(responses[site]);
    });
  });
}

// Function to cache Gemini response
function cacheGeminiResponse(site, isDistracting) {
  chrome.storage.sync.get(['geminiResponses'], function(result) {
    const responses = result.geminiResponses || {};
    responses[site] = {
      isDistracting,
      timestamp: Date.now()
    };
    chrome.storage.sync.set({ geminiResponses: responses });
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

// Function to add a log entry
function addLogEntry(site, response, isBlocked) {
  chrome.storage.sync.get(['siteCheckLogs'], function(result) {
    const logs = result.siteCheckLogs || [];
    const newLog = {
      site: site,
      response: response,
      action: isBlocked ? 'Blocked' : 'Allowed',
      source: 'Background Check'
    };
    
    // Add to beginning of array
    logs.unshift(newLog);
    
    // Keep only last 10 entries
    if (logs.length > 10) {
      logs.pop();
    }
    
    // Save back to storage
    chrome.storage.sync.set({ siteCheckLogs: logs });
  });
}

// Function to check with Gemini if a site is distracting
async function checkWithGemini(site) {
  try {
    // First check if we have a cached response
    const cachedResponse = await getCachedGeminiResponse(site);
    if (cachedResponse) {
      addLogEntry(site, cachedResponse.isDistracting ? 'Yes (cached)' : 'No (cached)', cachedResponse.isDistracting);
      return cachedResponse.isDistracting;
    }

    const result = await chrome.storage.sync.get(['apiKey']);
    if (!result.apiKey) {
      addLogEntry(site, 'No API key configured', false);
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
            text: `Is ${site} a distracting website that should be blocked to maintain focus? Evaluate basis of following categories: Entertainment, Social Media, News, Shopping, Gambling, Gaming, Sports. Answer with only 'yes' or 'no'.`
          }]
        }]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      addLogEntry(site, `Error: ${errorText}`, false);
      throw new Error('API request failed');
    }

    const data = await response.json();
    const answer = data.candidates[0].content.parts[0].text.toLowerCase().trim();
    const isDistracting = answer === 'yes';
    
    // Cache the response
    cacheGeminiResponse(site, isDistracting);
    
    addLogEntry(site, answer, isDistracting);
    return isDistracting;
  } catch (error) {
    console.error('Error checking site with Gemini:', error);
    addLogEntry(site, `Error: ${error.message}`, false);
    return false;
  }
}

// Function to check if a URL should be blocked
async function shouldBlock(url) {
  // Don't block Chrome internal pages
  if (isChromeInternalPage(url)) {
    addLogEntry(url, 'Not checked (Chrome internal page)', false);
    return false;
  }

  const hostname = new URL(url).hostname.toLowerCase();
  
  // First check if it's in the blocked list
  const isInBlockedList = await isBlocked(url);
  if (isInBlockedList) {
    addLogEntry(hostname, 'Yes (in blocked list)', true);
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

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkIfDistracting') {
    checkWithGemini(request.site)
      .then(isDistracting => {
        sendResponse({ isDistracting });
      })
      .catch(error => {
        console.error('Error checking site:', error);
        sendResponse({ isDistracting: false, error: error.message });
      });
    return true; // Will respond asynchronously
  }
});