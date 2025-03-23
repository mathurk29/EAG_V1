document.addEventListener('DOMContentLoaded', function() {
  const siteInput = document.getElementById('siteInput');
  const addButton = document.getElementById('addSite');
  const blockCurrentButton = document.getElementById('blockCurrentSite');
  const blockedSitesDiv = document.getElementById('blockedSites');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const saveApiKeyButton = document.getElementById('saveApiKey');
  const apiKeyDisplay = document.getElementById('apiKeyDisplay');
  const editApiKeyButton = document.getElementById('editApiKey');
  const testApiKeyButton = document.getElementById('testApiKey');
  const apiStatus = document.getElementById('apiStatus');
  const logContainer = document.getElementById('logContainer');
  const clearLogsButton = document.getElementById('clearLogs');

  // Load blocked sites and API key when popup opens
  loadBlockedSites();
  loadApiKey();
  loadLogs();

  // Function to add a log entry
  function addLogEntry(site, response, isBlocked, source = 'Manual Check') {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const siteSpan = document.createElement('div');
    siteSpan.className = 'log-site';
    siteSpan.textContent = `Site: ${site}`;
    
    const responseSpan = document.createElement('div');
    responseSpan.className = 'log-response';
    responseSpan.textContent = `Response: ${response}`;
    
    const actionSpan = document.createElement('div');
    actionSpan.className = 'log-response';
    actionSpan.textContent = `Action: ${isBlocked ? 'Blocked' : 'Allowed'} (${source})`;
    
    logEntry.appendChild(siteSpan);
    logEntry.appendChild(responseSpan);
    logEntry.appendChild(actionSpan);
    
    // Add to beginning of log container
    logContainer.insertBefore(logEntry, logContainer.firstChild);
    
    // Keep only last 10 entries
    while (logContainer.children.length > 10) {
      logContainer.removeChild(logContainer.lastChild);
    }
    
    // Save logs to storage
    saveLogs();
  }

  // Function to save logs to storage
  function saveLogs() {
    const logs = Array.from(logContainer.children).map(entry => ({
      site: entry.querySelector('.log-site').textContent.replace('Site: ', ''),
      response: entry.querySelector('.log-response').textContent.replace('Response: ', ''),
      action: entry.querySelector('.log-response:last-child').textContent.split(' (')[0].replace('Action: ', ''),
      source: entry.querySelector('.log-response:last-child').textContent.match(/\((.*)\)$/)[1]
    }));
    chrome.storage.sync.set({ siteCheckLogs: logs });
  }

  // Function to load logs from storage
  function loadLogs() {
    chrome.storage.sync.get(['siteCheckLogs'], function(result) {
      const logs = result.siteCheckLogs || [];
      logs.forEach(log => {
        addLogEntry(log.site, log.response, log.action === 'Blocked', log.source);
      });
    });
  }

  // API Key Management
  saveApiKeyButton.addEventListener('click', function() {
    const apiKey = apiKeyInput.value.trim();
    if (apiKey) {
      chrome.storage.sync.set({ apiKey: apiKey }, function() {
        showFeedback('API Key saved successfully');
        loadApiKey();
      });
    }
  });

  editApiKeyButton.addEventListener('click', function() {
    apiKeyDisplay.style.display = 'none';
    document.getElementById('apiKeySection').style.display = 'block';
  });

  testApiKeyButton.addEventListener('click', async function() {
    const result = await chrome.storage.sync.get(['apiKey']);
    const apiKey = result.apiKey;
    
    if (!apiKey) {
      showApiStatus('Please save an API key first', 'error');
      return;
    }

    try {
      const response = await testGeminiConnection(apiKey);
      if (response.success) {
        showApiStatus('Connected to Gemini API successfully', 'connected');
        addLogEntry('Test Connection', 'Success', false, 'API Test');
      } else {
        showApiStatus('Failed to connect to Gemini API', 'error');
        addLogEntry('Test Connection', 'Failed', false, 'API Test');
      }
    } catch (error) {
      showApiStatus('Error testing connection: ' + error.message, 'error');
      addLogEntry('Test Connection', 'Error: ' + error.message, false, 'API Test');
    }
  });

  // Load API Key
  function loadApiKey() {
    chrome.storage.sync.get(['apiKey'], function(result) {
      if (result.apiKey) {
        apiKeyDisplay.style.display = 'block';
        document.getElementById('apiKeySection').style.display = 'none';
      } else {
        apiKeyDisplay.style.display = 'none';
        document.getElementById('apiKeySection').style.display = 'block';
      }
    });
  }

  // Test Gemini Connection
  async function testGeminiConnection(apiKey) {
    try {
      console.log('Making API request to Gemini Flash 2.0...');
      const response = await fetch(`https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: "Test connection"
            }]
          }]
        })
      });

      console.log('API Response status:', response.status);
      console.log('API Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error response:', errorText);
        throw new Error(`API request failed with status ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('API Response data:', data);
      return { success: true, data };
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  // Show API Status
  function showApiStatus(message, type) {
    apiStatus.textContent = message;
    apiStatus.className = `api-status ${type}`;
    apiStatus.style.display = 'block';
  }

  // Add new site to block
  addButton.addEventListener('click', function() {
    addSite();
  });

  // Block current site button
  blockCurrentButton.addEventListener('click', async function() {
    chrome.tabs.query({ active: true, currentWindow: true }, async function(tabs) {
      if (tabs[0]) {
        const url = new URL(tabs[0].url);
        // Don't block chrome:// URLs or the blocked.html page
        if (url.protocol.startsWith('http')) {
          const hostname = url.hostname.replace(/^www\./, '');
          addSite(hostname);
          addLogEntry(hostname, 'Manually blocked by user', true, 'Manual Block');
        } else {
          showFeedback('Cannot block this type of page');
          addLogEntry(url.href, 'Not checked (Chrome internal page)', false, 'System');
        }
      }
    });
  });

  // Also trigger add when Enter key is pressed
  siteInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      addSite();
    }
  });

  function addSite(predefinedSite = null) {
    let site = predefinedSite || siteInput.value.trim().toLowerCase();
    
    // Clean up the input URL
    site = site.replace(/^https?:\/\//, ''); // Remove http:// or https://
    site = site.replace(/^www\./, ''); // Remove www.
    site = site.split('/')[0]; // Remove any paths
    
    if (site) {
      chrome.storage.sync.get(['blockedSites'], function(result) {
        const blockedSites = result.blockedSites || [];
        if (!blockedSites.includes(site)) {
          blockedSites.push(site);
          chrome.storage.sync.set({ blockedSites: blockedSites }, function() {
            console.log('Site added:', site);
            loadBlockedSites();
            if (!predefinedSite) {
              siteInput.value = '';
            }
            showFeedback(`Added ${site} to blocked list`);
          });
        } else {
          showFeedback(`${site} is already blocked`);
        }
      });
    }
  }

  // Function to show feedback to user
  function showFeedback(message) {
    const feedback = document.createElement('div');
    feedback.style.cssText = `
      position: fixed;
      bottom: 10px;
      left: 50%;
      transform: translateX(-50%);
      background-color: #333;
      color: white;
      padding: 8px 16px;
      border-radius: 4px;
      font-size: 14px;
      z-index: 1000;
    `;
    feedback.textContent = message;
    document.body.appendChild(feedback);
    setTimeout(() => {
      feedback.remove();
    }, 2000);
  }

  // Load and display blocked sites
  function loadBlockedSites() {
    chrome.storage.sync.get(['blockedSites'], function(result) {
      const blockedSites = result.blockedSites || [];
      console.log('Current blocked sites:', blockedSites);
      blockedSitesDiv.innerHTML = '';
      
      blockedSites.forEach(site => {
        const siteDiv = document.createElement('div');
        siteDiv.className = 'site-item';
        
        const siteText = document.createElement('span');
        siteText.textContent = site;
        
        const removeButton = document.createElement('button');
        removeButton.textContent = 'Remove';
        removeButton.className = 'remove-btn';
        removeButton.addEventListener('click', function() {
          removeSite(site);
        });
        
        siteDiv.appendChild(siteText);
        siteDiv.appendChild(removeButton);
        blockedSitesDiv.appendChild(siteDiv);
      });
    });
  }

  // Remove a site from blocked list
  function removeSite(siteToRemove) {
    chrome.storage.sync.get(['blockedSites'], function(result) {
      const blockedSites = result.blockedSites || [];
      const updatedSites = blockedSites.filter(site => site !== siteToRemove);
      chrome.storage.sync.set({ blockedSites: updatedSites }, function() {
        console.log('Site removed:', siteToRemove);
        loadBlockedSites();
        showFeedback(`Removed ${siteToRemove} from blocked list`);
      });
    });
  }

  // Clear logs button functionality
  clearLogsButton.addEventListener('click', function() {
    logContainer.innerHTML = '';
    chrome.storage.sync.set({ siteCheckLogs: [] }, function() {
      showFeedback('Logs cleared successfully');
    });
  });
});