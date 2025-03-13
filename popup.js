document.addEventListener('DOMContentLoaded', function() {
  const siteInput = document.getElementById('siteInput');
  const addButton = document.getElementById('addSite');
  const blockedSitesDiv = document.getElementById('blockedSites');

  // Load blocked sites when popup opens
  loadBlockedSites();

  // Add new site to block
  addButton.addEventListener('click', function() {
    const site = siteInput.value.trim().toLowerCase();
    if (site) {
      chrome.storage.sync.get(['blockedSites'], function(result) {
        const blockedSites = result.blockedSites || [];
        if (!blockedSites.includes(site)) {
          blockedSites.push(site);
          chrome.storage.sync.set({ blockedSites: blockedSites }, function() {
            loadBlockedSites();
            siteInput.value = '';
          });
        }
      });
    }
  });

  // Load and display blocked sites
  function loadBlockedSites() {
    chrome.storage.sync.get(['blockedSites'], function(result) {
      const blockedSites = result.blockedSites || [];
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
        loadBlockedSites();
      });
    });
  }
}); 