// SQL Results JavaScript - Simplified
let allResults = [];
let filteredResults = [];

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadCachedDataOnLoad();
});

function initializeEventListeners() {
    document.getElementById('fetchDataBtn').addEventListener('click', fetchDataFromDB);
    document.getElementById('loadCachedBtn').addEventListener('click', loadCachedData);
    document.getElementById('globalSearch').addEventListener('input', performGlobalSearch);
}

function showLoading(message = 'Processing...') {
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showToast(message, type = 'info') {
    // Simple alert for now - can be enhanced later
    if (type === 'error') {
        alert('Error: ' + message);
    } else {
        console.log(type + ': ' + message);
    }
}

function fetchDataFromDB() {
    const niftyRank = document.getElementById('niftyRankInput').value || '600';
    
    showLoading('Fetching data...');
    
    fetch('/sql-results/api/fetch-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nifty_rank: niftyRank })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            allResults = data.results;
            filteredResults = [...allResults];
            displayResults();
            updateLastFetch(data.cache_info);
        } else {
            showToast(data.error || 'Unknown error', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

function loadCachedData() {
    showLoading('Loading cache...');
    
    fetch('/sql-results/api/get-cached-data')
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            allResults = data.results;
            filteredResults = [...allResults];
            displayResults();
            updateLastFetch(data.cache_info);
        } else {
            showToast(data.error || 'No cached data', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Error: ' + error.message, 'error');
    });
}

function loadCachedDataOnLoad() {
    fetch('/sql-results/api/get-cached-data')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.results.length > 0) {
            allResults = data.results;
            filteredResults = [...allResults];
            displayResults();
            updateLastFetch(data.cache_info);
        }
    })
    .catch(() => {});
}

function updateLastFetch(cacheInfo) {
    const badge = document.getElementById('lastFetch');
    if (cacheInfo && cacheInfo.last_fetch) {
        const date = new Date(cacheInfo.last_fetch);
        badge.textContent = `Last: ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
        badge.className = 'badge bg-success';
    } else {
        badge.textContent = 'No data';
        badge.className = 'badge bg-secondary';
    }
}

function displayResults() {
    const container = document.getElementById('resultsContainer');
    
    if (filteredResults.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-database fa-3x mb-3"></i>
                <h4>No Data Available</h4>
                <p>Click "Fetch Data" to load from database or "Load Cache" to view saved results.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    filteredResults.forEach((result, index) => {
        const queryId = `query-${index}`;
        
        html += `
            <div class="query-section">
                <div class="query-header" onclick="toggleQuery('${queryId}')">
                    <div>
                        <strong>${result.query_name}</strong>
                        <span class="badge bg-light text-dark ms-2">${result.row_count} rows</span>
                    </div>
                    <i class="fas fa-chevron-down" id="${queryId}-icon"></i>
                </div>
                <div class="query-content" id="${queryId}">
                    <div class="table-wrapper">
                        <table class="table table-striped table-hover table-sm">
                            <thead class="table-dark">
                                <tr>
                                    ${result.columns.map(col => `<th>${col}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${generateTableRows(result.rows, result.columns)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function generateTableRows(rows, columns) {
    return rows.map(row => {
        const cells = columns.map(col => {
            let value = row[col] || '';
            
            // Symbol hyperlink
            if (col.toUpperCase() === 'SYMBOL' && value.trim()) {
                const tradingViewUrl = `https://in.tradingview.com/chart/?symbol=NSE:${value.trim()}`;
                return `<td><a href="#" onclick="openTradingViewPopup('${tradingViewUrl}', '${value}'); return false;" class="symbol-link">${value}</a></td>`;
            }
            
            return `<td>${value}</td>`;
        }).join('');
        
        return `<tr>${cells}</tr>`;
    }).join('');
}

function toggleQuery(queryId) {
    const content = document.getElementById(queryId);
    const icon = document.getElementById(queryId + '-icon');
    
    if (content.classList.contains('show')) {
        content.classList.remove('show');
        icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
    } else {
        content.classList.add('show');
        icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
    }
}

function performGlobalSearch() {
    const searchTerm = document.getElementById('globalSearch').value.toLowerCase();
    
    if (!searchTerm.trim()) {
        filteredResults = [...allResults];
    } else {
        filteredResults = allResults.map(result => {
            const filteredRows = result.rows.filter(row => {
                return result.columns.some(col => {
                    const cellValue = (row[col] || '').toString().toLowerCase();
                    return cellValue.includes(searchTerm);
                });
            });
            
            if (filteredRows.length > 0) {
                return { ...result, rows: filteredRows, row_count: filteredRows.length };
            }
            return null;
        }).filter(result => result !== null);
    }
    
    displayResults();
}

function openTradingViewPopup(url, symbol) {
    const popupWidth = 1700;
    const popupHeight = 900;
    const left = (screen.width - popupWidth) / 2;
    const top = (screen.height - popupHeight) / 2;
    
    const features = [
        `width=${popupWidth}`,
        `height=${popupHeight}`,
        `left=${left}`,
        `top=${top}`,
        'resizable=yes',
        'scrollbars=yes',
        'toolbar=no',
        'menubar=no',
        'location=no',
        'status=no'
    ].join(',');
    
    const popup = window.open(url, `tradingview_${symbol}`, features);
    if (popup) {
        popup.focus();
    } else {
        alert('Popup blocked! Please allow popups for this site.');
        window.open(url, '_blank');
    }
}

// Global functions
window.openTradingViewPopup = openTradingViewPopup;
window.toggleQuery = toggleQuery;
