let activityLog = [];

function addToLog(message, type = 'info') {
  const timestamp = new Date().toLocaleString();
  const entry = { message, type, timestamp };
  activityLog.unshift(entry);
  
  // Keep only last 50 entries
  if (activityLog.length > 50) {
    activityLog = activityLog.slice(0, 50);
  }
  
  updateActivityDisplay();
}

function updateActivityDisplay() {
  const logContainer = document.getElementById('activityLog');
  
  if (activityLog.length === 0) {
    logContainer.innerHTML = '<div class="text-gray-400 text-sm">No recent activity</div>';
    return;
  }

  logContainer.innerHTML = activityLog.map(entry => {
    const colorClass = {
      'info': 'text-blue-400',
      'success': 'text-green-400',
      'warning': 'text-yellow-400',
      'error': 'text-red-400'
    }[entry.type] || 'text-gray-400';

    return `
      <div class="flex justify-between items-start py-2 border-b border-gray-700 last:border-b-0">
        <div class="flex-1">
          <div class="${colorClass} text-sm">${entry.message}</div>
        </div>
        <div class="text-xs text-gray-500 ml-4">${entry.timestamp}</div>
      </div>
    `;
  }).join('');
}

function showMessage(message, type = 'info') {
  const messageDiv = document.getElementById('statusMessage');
  const colors = {
    'info': 'bg-blue-900 text-blue-300 border-blue-700',
    'success': 'bg-green-900 text-green-300 border-green-700',
    'warning': 'bg-yellow-900 text-yellow-300 border-yellow-700',
    'error': 'bg-red-900 text-red-300 border-red-700'
  };
  
  messageDiv.className = `mt-4 p-3 rounded border ${colors[type]}`;
  messageDiv.textContent = message;
  messageDiv.classList.remove('hidden');
  
  setTimeout(() => {
    messageDiv.classList.add('hidden');
  }, 5000);

  // Add to activity log
  addToLog(message, type);
}

async function loadStatistics() {
  try {
    const response = await fetch('/api/admin/stats');
    const stats = await response.json();
    
    if (stats.success) {
      document.getElementById('totalMovies').textContent = stats.data.total_movies;
      document.getElementById('verifiedMovies').textContent = stats.data.verified_movies;
      document.getElementById('ageRestrictedMovies').textContent = stats.data.age_restricted_movies;
      document.getElementById('unverifiedMovies').textContent = stats.data.unverified_movies;
      document.getElementById('cacheCount').textContent = stats.data.cache_entries;
      document.getElementById('cacheCountMain').textContent = stats.data.cache_entries;
      
      // Cache hit rate calculation
      if (stats.data.total_movies > 0) {
        const hitRate = Math.round((stats.data.cache_entries / stats.data.total_movies) * 100);
        document.getElementById('cacheHitRate').textContent = `${hitRate}%`;
      } else {
        document.getElementById('cacheHitRate').textContent = '0%';
      }
      
      // Oldest cache entry
      if (stats.data.oldest_cache) {
        const oldestDate = new Date(stats.data.oldest_cache);
        const now = new Date();
        const daysDiff = Math.floor((now - oldestDate) / (1000 * 60 * 60 * 24));
        document.getElementById('oldestCache').textContent = `${daysDiff} days ago`;
      } else {
        document.getElementById('oldestCache').textContent = 'No cache';
      }
      
      if (stats.data.last_verification) {
        document.getElementById('lastVerification').textContent = new Date(stats.data.last_verification).toLocaleString();
      } else {
        document.getElementById('lastVerification').textContent = 'Never';
      }
      
      if (stats.data.last_age_check) {
        document.getElementById('lastAgeCheck').textContent = new Date(stats.data.last_age_check).toLocaleString();
      } else {
        document.getElementById('lastAgeCheck').textContent = 'Never';
      }
    }
  } catch (error) {
    showMessage('Failed to load statistics', 'error');
  }
}

// Initialize admin functionality
document.addEventListener('DOMContentLoaded', function() {
  // Verify All Movies
  document.getElementById('verifyAllBtn').addEventListener('click', async () => {
    try {
      const button = document.getElementById('verifyAllBtn');
      const status = document.getElementById('verificationStatus');
      
      button.disabled = true;
      status.classList.remove('hidden');
      
      const response = await fetch('/api/verify-all-movies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      if (result.success) {
        showMessage('🔄 Verification started! This may take a few minutes.', 'success');
        addToLog('Started verification of all movies', 'info');
      } else {
        showMessage('Error starting verification', 'error');
      }
    } catch (error) {
      showMessage('Error starting verification', 'error');
    } finally {
      document.getElementById('verifyAllBtn').disabled = false;
      document.getElementById('verificationStatus').classList.add('hidden');
    }
  });

  // Check Age Restrictions
  document.getElementById('checkAgeRestrictionsBtn').addEventListener('click', async () => {
    try {
      const button = document.getElementById('checkAgeRestrictionsBtn');
      const status = document.getElementById('ageCheckStatus');
      
      button.disabled = true;
      status.classList.remove('hidden');
      
      const response = await fetch('/api/check-age-restrictions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      if (result.success) {
        const restrictedCount = result.results.filter(r => r.age_restricted).length;
        showMessage(`🔍 Age restriction check complete! Found ${restrictedCount} age-restricted videos.`, 'success');
        addToLog(`Age restriction check completed: ${restrictedCount} restricted videos found`, 'success');
        loadStatistics(); // Refresh stats
      } else {
        showMessage('Error checking age restrictions', 'error');
      }
    } catch (error) {
      showMessage('Error checking age restrictions', 'error');
    } finally {
      document.getElementById('checkAgeRestrictionsBtn').disabled = false;
      document.getElementById('ageCheckStatus').classList.add('hidden');
    }
  });

  // Clear All Cache
  document.getElementById('clearAllCacheBtn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear all cached movie information?')) {
      return;
    }
    
    try {
      const response = await fetch('/api/admin/clear-all-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      if (result.success) {
        showMessage('🗑️ All cache cleared successfully', 'success');
        addToLog('Cleared all movie info cache', 'warning');
        loadStatistics();
      } else {
        showMessage('Error clearing cache', 'error');
      }
    } catch (error) {
      showMessage('Error clearing cache', 'error');
    }
  });

  // Refresh All Cache
  document.getElementById('refreshAllCacheBtn').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to refresh all cached movie information? This will take a while.')) {
      return;
    }
    
    try {
      const response = await fetch('/api/admin/refresh-all-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      if (result.success) {
        showMessage('🔄 Cache refresh started! This may take several minutes.', 'success');
        addToLog('Started cache refresh for all movies', 'info');
      } else {
        showMessage('Error starting cache refresh', 'error');
      }
    } catch (error) {
      showMessage('Error starting cache refresh', 'error');
    }
  });

  // Load initial data
  loadStatistics();
  
  // Refresh stats every 30 seconds
  setInterval(loadStatistics, 30000);
});
