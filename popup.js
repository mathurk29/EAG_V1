document.addEventListener('DOMContentLoaded', function() {
  const siteInput = document.getElementById('siteInput');
  const addButton = document.getElementById('addSite');
  const blockCurrentButton = document.getElementById('blockCurrentSite');
  const blockedSitesDiv = document.getElementById('blockedSites');
  const collectionsGrid = document.getElementById('collectionsGrid');

  // Load blocked sites and collections when popup opens
  loadBlockedSites();
  loadCollections();

  // Add new site to block
  addButton.addEventListener('click', function() {
    addSite();
  });

  // Block current site button
  blockCurrentButton.addEventListener('click', function() {
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (tabs[0]) {
        const url = new URL(tabs[0].url);
        // Don't block chrome:// URLs or the blocked.html page
        if (url.protocol.startsWith('http')) {
          const hostname = url.hostname.replace(/^www\./, '');
          addSite(hostname);
        } else {
          alert('Cannot block this type of page');
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
            console.log('Site added:', site); // Debug log
            loadBlockedSites();
            if (!predefinedSite) {
              siteInput.value = '';
            }
            // Show feedback to user
            showFeedback(`Added ${site} to blocked list`);
            updateCollectionStates(blockedSites);
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
      console.log('Current blocked sites:', blockedSites); // Debug log
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
        console.log('Site removed:', siteToRemove); // Debug log
        loadBlockedSites();
        showFeedback(`Removed ${siteToRemove} from blocked list`);
        updateCollectionStates(updatedSites);
      });
    });
  }

  // Function to load collections
  async function loadCollections() {
    const result = await chrome.storage.sync.get(['blockedSites', 'activeCollections']);
    const blockedSites = result.blockedSites || [];
    const activeCollections = result.activeCollections || {};

    collectionsGrid.innerHTML = '';

    Object.entries(siteCollections).forEach(([key, collection]) => {
      const collectionItem = document.createElement('div');
      collectionItem.className = 'collection-item';

      // Create checkbox
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'collection-checkbox';
      checkbox.id = `collection-${key}`;
      checkbox.checked = activeCollections[key] || false;

      // Create label
      const label = document.createElement('label');
      label.className = 'collection-label';
      label.htmlFor = `collection-${key}`;
      label.textContent = collection.name;

      // Create count badge
      const count = document.createElement('span');
      count.className = 'collection-count';
      count.textContent = collection.sites.length;

      // Create sites preview
      const sites = document.createElement('div');
      sites.className = 'collection-sites';
      sites.textContent = collection.sites.slice(0, 3).join(', ') + 
        (collection.sites.length > 3 ? ' ...' : '');

      // Add event listener to checkbox
      checkbox.addEventListener('change', () => toggleCollection(key, collection, checkbox.checked));

      collectionItem.appendChild(checkbox);
      collectionItem.appendChild(label);
      collectionItem.appendChild(count);
      collectionItem.appendChild(sites);
      collectionsGrid.appendChild(collectionItem);
    });
  }

  // Function to toggle collection
  async function toggleCollection(key, collection, isEnabled) {
    try {
      const result = await chrome.storage.sync.get(['blockedSites', 'activeCollections']);
      let blockedSites = result.blockedSites || [];
      let activeCollections = result.activeCollections || {};

      if (isEnabled) {
        // Add sites from collection
        collection.sites.forEach(site => {
          if (!blockedSites.includes(site)) {
            blockedSites.push(site);
          }
        });
        activeCollections[key] = true;
        showFeedback(`Enabled ${collection.name} collection`);
      } else {
        // Remove sites from collection
        blockedSites = blockedSites.filter(site => 
          !collection.sites.includes(site)
        );
        activeCollections[key] = false;
        showFeedback(`Disabled ${collection.name} collection`);
      }

      await chrome.storage.sync.set({ 
        blockedSites,
        activeCollections
      });
      loadBlockedSites();
    } catch (error) {
      console.error('Error toggling collection:', error);
      showFeedback('Error updating sites');
    }
  }

  // When manually adding or removing sites, we should check if they belong to any collection
  async function updateCollectionStates(sites) {
    const result = await chrome.storage.sync.get(['activeCollections']);
    let activeCollections = result.activeCollections || {};

    Object.entries(siteCollections).forEach(([key, collection]) => {
      // Check if all sites in the collection are blocked
      const allSitesBlocked = collection.sites.every(site => 
        sites.includes(site)
      );
      activeCollections[key] = allSitesBlocked;
    });

    await chrome.storage.sync.set({ activeCollections });
    loadCollections();
  }
}); 