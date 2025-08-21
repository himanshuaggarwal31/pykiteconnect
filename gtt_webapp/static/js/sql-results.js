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
    
    // Add event delegation for toggle buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.query-header')) {
            const header = e.target.closest('.query-header');
            const queryId = header.getAttribute('data-query-id');
            if (queryId) {
                console.log('Toggling query:', queryId);
                toggleQuery(queryId);
            }
        }
        
        // Handle GTT buttons (Add Buy GTT or Add Sell GTT)
        if (e.target.classList.contains('btn-add-buy-gtt') || e.target.parentElement.classList.contains('btn-add-buy-gtt')) {
            const button = e.target.classList.contains('btn-add-buy-gtt') ? e.target : e.target.parentElement;
            const symbol = button.getAttribute('data-symbol');
            const companyName = button.getAttribute('data-company-name');
            const niftyRank = button.getAttribute('data-nifty-rank') || null;
            const lastPrice = parseFloat(button.getAttribute('data-price') || 0);
            
            addGTTOrder(symbol, companyName, niftyRank, 'BUY', 'single', lastPrice);
            e.preventDefault();
            e.stopPropagation();
        }
        
        if (e.target.classList.contains('btn-add-sell-gtt') || e.target.parentElement.classList.contains('btn-add-sell-gtt')) {
            const button = e.target.classList.contains('btn-add-sell-gtt') ? e.target : e.target.parentElement;
            const symbol = button.getAttribute('data-symbol');
            const companyName = button.getAttribute('data-company-name');
            const niftyRank = button.getAttribute('data-nifty-rank') || null;
            const lastPrice = parseFloat(button.getAttribute('data-price') || 0);
            
            openSellTypeModal(symbol, companyName, niftyRank, lastPrice);
            e.preventDefault();
            e.stopPropagation();
        }
    });
    
    // Make toggleQuery available globally for both approaches
    window.toggleQuery = toggleQuery;
    
    // Initialize the GTT Order Modal
    initializeGTTOrderModal();
    initializeSellTypeModal();
}

function showLoading(message = 'Processing...') {
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    console.log('hideLoading called');
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
        console.log('Loading overlay hidden');
    } else {
        console.error('Loading overlay element not found');
    }
}

function showToast(message, type = 'info') {
    // Create a toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }
    
    // Set the bootstrap color class based on type
    const bgClass = type === 'error' ? 'bg-danger' : 
                    type === 'success' ? 'bg-success' : 
                    type === 'warning' ? 'bg-warning' : 'bg-info';
    
    // Create a unique ID for this toast
    const toastId = 'toast-' + Date.now();
    
    // Create the toast HTML
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} text-white border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Add the toast to the container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Also log to console
    console.log(`${type.toUpperCase()}: ${message}`);
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
    
    // Force hide loading overlay when displaying results
    hideLoading();
    
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
                <div class="query-header" data-query-id="${queryId}" style="cursor: pointer;">
                    <div>
                        <strong>${result.query_name}</strong>
                        <span class="badge bg-light text-dark ms-2">${result.row_count} rows</span>
                    </div>
                    <i class="fas fa-chevron-down" id="${queryId}-icon"></i>
                </div>
                <div class="query-content" id="${queryId}">
                    <div class="table-wrapper">
                        <table class="table table-striped table-hover table-sm table-compact">
                            <thead class="table-dark">
                                <tr>
                                    ${result.columns.map(col => {
                                        let className = '';
                                        const colUpper = col.toUpperCase();
                                        if (colUpper === 'SYMBOL') className = 'symbol-col';
                                        else if (colUpper.includes('COMPANY') || colUpper.includes('NAME')) className = 'company-col';
                                        else if (colUpper.includes('PRICE') || colUpper.includes('CHANGE') || colUpper.includes('VOLUME') || colUpper.includes('RANK')) className = 'text-end';
                                        return `<th class="${className}">${col}</th>`;
                                    }).join('')}
                                    <th class="actions-col">Actions</th>
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
    
    // Ensure all tables start in collapsed state
    initializeTableStates();
}

function initializeTableStates() {
    // Set all query content divs to be explicitly hidden
    const queryContents = document.querySelectorAll('.query-content');
    queryContents.forEach(content => {
        content.style.display = 'none';
    });
    
    // Ensure all chevron icons are pointing down
    const chevronIcons = document.querySelectorAll('[id$="-icon"]');
    chevronIcons.forEach(icon => {
        icon.className = 'fas fa-chevron-down';
    });
}

function generateTableRows(rows, columns) {
    return rows.map(row => {
        // Extract values needed for the GTT buttons
        const symbol = row['SYMBOL'] || '';
        const companyName = row['COMPANY_NAME'] || '';
        const niftyRank = row['NIFTY_RANK'] || '';
        const lastPrice = row['LAST_PRICE'] || row['CLOSE_PRICE'] || 0;
        
        // Create table cells for existing data
        const cells = columns.map(col => {
            let value = row[col] || '';
            let className = '';
            const colUpper = col.toUpperCase();
            
            // Determine CSS class based on column type
            if (colUpper === 'SYMBOL') className = 'symbol-col';
            else if (colUpper.includes('COMPANY') || colUpper.includes('NAME')) className = 'company-col';
            else if (colUpper.includes('PRICE') || colUpper.includes('CHANGE') || colUpper.includes('VOLUME') || colUpper.includes('RANK')) className = 'text-end';
            
            // Symbol hyperlink
            if (colUpper === 'SYMBOL' && value.trim()) {
                const tradingViewUrl = `https://in.tradingview.com/chart/?symbol=NSE:${value.trim()}`;
                return `<td class="${className}"><a href="#" onclick="openTradingViewPopup('${tradingViewUrl}', '${value}'); return false;" class="symbol-link">${value}</a></td>`;
            }
            
            return `<td class="${className}">${value}</td>`;
        }).join('');
        
        // Add action buttons column
        const actionBtns = `
            <td class="actions-col">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-success btn-add-buy-gtt" title="Add Buy GTT"
                        data-symbol="${symbol}" 
                        data-company-name="${companyName}" 
                        data-nifty-rank="${niftyRank}"
                        data-price="${lastPrice}">
                        <i class="fas fa-plus"></i> BUY
                    </button>
                    <button class="btn btn-danger btn-add-sell-gtt" title="Add Sell GTT"
                        data-symbol="${symbol}" 
                        data-company-name="${companyName}" 
                        data-nifty-rank="${niftyRank}"
                        data-price="${lastPrice}">
                        <i class="fas fa-plus"></i> SELL
                    </button>
                </div>
            </td>
        `;
        
        return `<tr>${cells}${actionBtns}</tr>`;
    }).join('');
}

function toggleQuery(queryId) {
    console.log('toggleQuery called with:', queryId);
    const content = document.getElementById(queryId);
    const icon = document.getElementById(queryId + '-icon');
    
    console.log('Found content element:', content);
    console.log('Found icon element:', icon);
    
    if (!content || !icon) {
        console.error('Could not find elements for queryId:', queryId);
        return;
    }
    
    // Check actual computed display style, not just inline style
    const computedDisplay = window.getComputedStyle(content).display;
    const isVisible = computedDisplay === 'block' && content.style.display !== 'none';
    
    if (isVisible) {
        content.style.display = 'none';
        icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
        console.log('Collapsed:', queryId);
    } else {
        content.style.display = 'block';
        content.style.background = 'white';
        content.style.border = 'none';
        content.style.padding = '0';
        icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
        console.log('Expanded:', queryId);
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

// Functions for handling GTT order creation

function initializeGTTOrderModal() {
    // Create the modal if it doesn't exist
    if (!document.getElementById('gttOrderModal')) {
        const modalHTML = `
        <div class="modal fade" id="gttOrderModal" tabindex="-1" aria-labelledby="gttOrderModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="gttOrderModalLabel">Create GTT Order</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="gttOrderForm">
                            <input type="hidden" id="orderSymbol" name="symbol">
                            <input type="hidden" id="orderCompanyName" name="company_name">
                            <input type="hidden" id="orderNiftyRank" name="nifty_rank">
                            <input type="hidden" id="orderType" name="order_type">
                            <input type="hidden" id="orderTriggerType" name="trigger_type">
                            
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <label for="orderSymbolDisplay" class="form-label">Symbol</label>
                                    <input type="text" class="form-control" id="orderSymbolDisplay" disabled>
                                </div>
                                <div class="col-md-8">
                                    <label for="orderCompanyNameDisplay" class="form-label">Company Name</label>
                                    <input type="text" class="form-control" id="orderCompanyNameDisplay" disabled>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <label for="orderLastPrice" class="form-label">Last Price</label>
                                    <input type="number" class="form-control" id="orderLastPrice" name="last_price" step="0.01" required>
                                </div>
                                <div class="col-md-4">
                                    <label for="orderTriggerPrice" class="form-label">Trigger Price</label>
                                    <input type="number" class="form-control" id="orderTriggerPrice" name="trigger_price" step="0.01" required>
                                </div>
                                <div class="col-md-4">
                                    <label for="orderTargetPrice" class="form-label">Target Price</label>
                                    <input type="number" class="form-control" id="orderTargetPrice" name="target_price" step="0.01">
                                </div>
                            </div>
                            
                            <div id="twoLegFields" style="display: none;">
                                <div class="row mb-3">
                                    <div class="col-md-4">
                                        <label for="orderStopLoss" class="form-label">Stop Loss Price</label>
                                        <input type="number" class="form-control" id="orderStopLoss" name="stop_loss" step="0.01">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-4">
                                    <label for="orderQuantity" class="form-label">Quantity</label>
                                    <input type="number" class="form-control" id="orderQuantity" name="quantity" min="1" value="0" required>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-12">
                                    <label for="orderNotes" class="form-label">Notes</label>
                                    <textarea class="form-control" id="orderNotes" name="notes" rows="2"></textarea>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="saveGttOrderBtn">Save Order</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add event listener to the save button
        document.getElementById('saveGttOrderBtn').addEventListener('click', saveGttOrder);
    }
}

function initializeSellTypeModal() {
    // Create the modal if it doesn't exist
    if (!document.getElementById('sellTypeModal')) {
        const modalHTML = `
        <div class="modal fade" id="sellTypeModal" tabindex="-1" aria-labelledby="sellTypeModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="sellTypeModalLabel">Select Sell Order Type</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-4">Select the type of sell order you want to create for <strong id="sellSymbolDisplay"></strong>:</p>
                        <div class="d-grid gap-3">
                            <button class="btn btn-lg btn-outline-danger" id="singleLegSellBtn">
                                <i class="fas fa-arrow-up me-2"></i>
                                <strong>Single-Leg Sell</strong>
                                <div class="small text-muted mt-1">Create a simple GTT order to sell at a specified trigger price</div>
                            </button>
                            <button class="btn btn-lg btn-outline-danger" id="twoLegSellBtn">
                                <i class="fas fa-exchange-alt me-2"></i>
                                <strong>Two-Leg Sell</strong>
                                <div class="small text-muted mt-1">Create a GTT with target price and stop loss</div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add event listeners for the sell type buttons
        document.getElementById('singleLegSellBtn').addEventListener('click', function() {
            const symbol = document.getElementById('sellSymbolDisplay').textContent;
            const modal = bootstrap.Modal.getInstance(document.getElementById('sellTypeModal'));
            modal.hide();
            
            const sellBtn = document.querySelector(`button.btn-add-sell-gtt[data-symbol="${symbol}"]`);
            if (sellBtn) {
                const companyName = sellBtn.getAttribute('data-company-name');
                const niftyRank = sellBtn.getAttribute('data-nifty-rank');
                const lastPrice = parseFloat(sellBtn.getAttribute('data-price'));
                
                addGTTOrder(symbol, companyName, niftyRank, 'SELL', 'single', lastPrice);
            }
        });
        
        document.getElementById('twoLegSellBtn').addEventListener('click', function() {
            const symbol = document.getElementById('sellSymbolDisplay').textContent;
            const modal = bootstrap.Modal.getInstance(document.getElementById('sellTypeModal'));
            modal.hide();
            
            const sellBtn = document.querySelector(`button.btn-add-sell-gtt[data-symbol="${symbol}"]`);
            if (sellBtn) {
                const companyName = sellBtn.getAttribute('data-company-name');
                const niftyRank = sellBtn.getAttribute('data-nifty-rank');
                const lastPrice = parseFloat(sellBtn.getAttribute('data-price'));
                
                addGTTOrder(symbol, companyName, niftyRank, 'SELL', 'two-leg', lastPrice);
            }
        });
    }
}

function openSellTypeModal(symbol, companyName, niftyRank, lastPrice) {
    // Set the symbol in the modal
    document.getElementById('sellSymbolDisplay').textContent = symbol;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('sellTypeModal'));
    modal.show();
}

function addGTTOrder(symbol, companyName, niftyRank, orderType, triggerType, lastPrice) {
    // Show loading toast
    showToast(`Checking ${symbol} orders...`, 'info');
    
    // Prepare request data
    const requestData = {
        symbol: symbol,
        order_type: orderType,
        trigger_type: triggerType
    };
    
    console.log('Sending request to check existing orders:', requestData);
    
    // First check if an order already exists
    fetch('/api/sql-results-gtt/add-gtt-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            // If order already exists, show it in edit mode
            if (data.exists) {
                showToast(`An order for ${symbol} (${orderType}) already exists. Opening in edit mode.`, 'info');
                openEditModal(data.order);
                return;
            }
            
            // If order was successfully created, show success message
            if (data.order_id) {
                showToast(`GTT order for ${symbol} created successfully!`, 'success');
                return;
            }
            
            // Otherwise, show the modal to configure the new order (this shouldn't happen with the new logic)
            showCreateModal(symbol, companyName, niftyRank, orderType, triggerType, lastPrice);
        } else {
            showToast(`Error: ${data.error || 'Failed to process GTT order'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error in addGTTOrder:', error);
        showToast(`Error: ${error.message}`, 'error');
    });
}

function showCreateModal(symbol, companyName, niftyRank, orderType, triggerType, lastPrice) {
    // Set up the modal with the provided values
    document.getElementById('orderSymbol').value = symbol;
    document.getElementById('orderCompanyName').value = companyName;
    document.getElementById('orderNiftyRank').value = niftyRank;
    document.getElementById('orderType').value = orderType;
    document.getElementById('orderTriggerType').value = triggerType;
    
    // Update display fields
    document.getElementById('orderSymbolDisplay').value = symbol;
    document.getElementById('orderCompanyNameDisplay').value = companyName;
    
    // Set the last price
    document.getElementById('orderLastPrice').value = lastPrice.toFixed(2);
    
    // Calculate suggested trigger price based on order type (10% below for buy, 10% above for sell)
    let triggerPrice;
    let targetPrice;
    
    if (orderType === 'BUY') {
        triggerPrice = (lastPrice * 0.9).toFixed(2);
        targetPrice = (lastPrice * 1.3).toFixed(2);
        document.getElementById('twoLegFields').style.display = 'none';
    } else { // SELL
        if (triggerType === 'single') {
            triggerPrice = (lastPrice * 1.1).toFixed(2);
            targetPrice = '';
            document.getElementById('twoLegFields').style.display = 'none';
        } else { // two-leg
            targetPrice = (lastPrice * 1.1).toFixed(2);
            triggerPrice = '';
            document.getElementById('orderStopLoss').value = (lastPrice * 0.9).toFixed(2);
            document.getElementById('twoLegFields').style.display = 'block';
        }
    }
    
    document.getElementById('orderTriggerPrice').value = triggerPrice;
    document.getElementById('orderTargetPrice').value = targetPrice;
    
    // Update modal title
    const action = orderType === 'BUY' ? 'Buy' : 'Sell';
    document.getElementById('gttOrderModalLabel').textContent = `Add ${action} GTT Order for ${symbol}`;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('gttOrderModal'));
    modal.show();
}

function openEditModal(order) {
    // Redirect to the custom GTT page and focus on this order
    window.location.href = `/custom-gtt/?search=${order.symbol}&order_type=${order.order_type}`;
}

// Variable to store sell modal data
let sellModalData = {
    symbol: '',
    companyName: '',
    niftyRank: '',
    lastPrice: 0
};

function handleSellTypeChoice(triggerType) {
    // Hide the sell type modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('sellTypeModal'));
    modal.hide();
    
    // Use the stored data for creating the sell order
    addGTTOrder(
        sellModalData.symbol, 
        sellModalData.companyName, 
        sellModalData.niftyRank, 
        'SELL', 
        triggerType, 
        sellModalData.lastPrice
    );
}

function openSellTypeModal(symbol, companyName, niftyRank, lastPrice) {
    // Store the data for later use
    sellModalData = {
        symbol,
        companyName,
        niftyRank,
        lastPrice
    };
    
    // Set the symbol in the modal
    document.getElementById('sellSymbolDisplay').textContent = symbol;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('sellTypeModal'));
    modal.show();
}

function saveGttOrder() {
    // Get form data
    const formData = new FormData(document.getElementById('gttOrderForm'));
    const orderData = {};
    
    // Convert form data to object
    for (const [key, value] of formData.entries()) {
        if (value) {
            orderData[key] = value;
        }
    }
    
    // Override trigger_type with the value from the dropdown
    const triggerTypeSelect = document.getElementById('orderTriggerTypeDisplay');
    if (triggerTypeSelect) {
        orderData.trigger_type = triggerTypeSelect.value;
    }
    
    // Check if this is an edit (has order_id)
    const orderId = document.getElementById('orderIdHidden') ? document.getElementById('orderIdHidden').value : null;
    const isEdit = orderId && orderId.trim() !== '';
    
    if (isEdit) {
        orderData.id = orderId;
    }
    
    // Basic validation
    if (!orderData.symbol) {
        showToast('Symbol is required', 'error');
        return;
    }
    
    if (!orderData.quantity || orderData.quantity <= 0) {
        // Set default quantity to 1
        orderData.quantity = 1;
    }
    
    // Validate trigger type specific fields
    if (orderData.order_type === 'BUY') {
        // BUY orders are always single leg
        orderData.trigger_type = 'single';
        if (!orderData.trigger_price) {
            showToast('Trigger price is required for BUY orders', 'error');
            return;
        }
        // Clear two-leg fields for BUY orders
        delete orderData.target_price;
        delete orderData.stop_loss;
    } else if (orderData.order_type === 'SELL') {
        // SELL orders can be single or two-leg
        if (orderData.trigger_type === 'single') {
            if (!orderData.trigger_price) {
                showToast('Trigger price is required for single leg SELL orders', 'error');
                return;
            }
            // Clear two-leg fields to avoid confusion
            delete orderData.target_price;
            delete orderData.stop_loss;
        } else if (orderData.trigger_type === 'two-leg') {
            if (!orderData.target_price || !orderData.stop_loss) {
                showToast('Both target price and stop loss are required for two-leg SELL orders', 'error');
                return;
            }
            // Clear single leg field to avoid confusion
            delete orderData.trigger_price;
        }
    }
    
    // Add default exchange if not present
    if (!orderData.exchange) {
        orderData.exchange = 'NSE';
    }
    
    // Add is_active and placed_on_kite
    orderData.is_active = 1;
    orderData.placed_on_kite = 0;
    
    console.log('Saving GTT order with data:', orderData);
    showToast(`${isEdit ? 'Updating' : 'Saving'} GTT order for ${orderData.symbol}...`, 'info');
    
    // Send to API
    fetch('/api/custom-gtt/save-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    })
    .then(response => {
        console.log('Save order response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Save order response data:', data);
        if (data.success) {
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('gttOrderModal'));
            if (modal) {
                modal.hide();
            } else {
                // If modal instance is not found, just hide it using jQuery or direct DOM manipulation
                const modalElement = document.getElementById('gttOrderModal');
                if (modalElement) {
                    modalElement.style.display = 'none';
                    // Also remove modal backdrop if present
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.parentNode.removeChild(backdrop);
                    }
                    document.body.classList.remove('modal-open');
                }
            }
            
            // Show success message
            const action = isEdit ? 'updated' : 'added';
            showToast(`GTT order for ${orderData.symbol} ${action} successfully`, 'success');
        } else {
            showToast(`Failed to save GTT order: ${data.error || 'Unknown error'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error in saveGttOrder:', error);
        showToast(`Error: ${error.message}`, 'error');
    });
}

// Function to open edit modal with existing order data
function openEditModal(order) {
    console.log('Opening edit modal with order:', order);
    
    // Update modal title
    const modalTitle = document.getElementById('gttOrderModalLabel');
    if (modalTitle) {
        modalTitle.textContent = 'Edit GTT Order';
    }
    
    // Fill the form with order data
    document.getElementById('orderSymbol').value = order.symbol || '';
    document.getElementById('orderCompanyName').value = order.company_name || '';
    document.getElementById('orderNiftyRank').value = order.nifty_rank || '';
    document.getElementById('orderType').value = order.order_type || '';
    document.getElementById('orderTriggerType').value = order.trigger_type || '';
    
    // Fill display fields
    document.getElementById('orderSymbolDisplay').value = order.symbol || '';
    document.getElementById('orderCompanyNameDisplay').value = order.company_name || '';
    document.getElementById('orderTriggerTypeDisplay').value = order.trigger_type || 'single';
    
    // Fill price and quantity fields
    document.getElementById('orderLastPrice').value = order.last_price || '';
    document.getElementById('orderQuantity').value = order.quantity || '';
    document.getElementById('orderNotes').value = order.notes || '';
    
    // Handle trigger type fields based on current selection and order type
    const triggerType = order.trigger_type || 'single';
    const orderType = order.order_type || 'BUY';
    
    // For BUY orders, force single leg
    if (orderType === 'BUY') {
        document.getElementById('orderTriggerTypeDisplay').value = 'single';
        toggleTriggerFields('single');
        document.getElementById('orderTriggerPrice').value = order.trigger_price || '';
    } else {
        // For SELL orders, respect the trigger type
        toggleTriggerFields(triggerType);
        if (triggerType === 'single') {
            document.getElementById('orderTriggerPrice').value = order.trigger_price || '';
        } else if (triggerType === 'two-leg') {
            document.getElementById('orderTargetPrice').value = order.target_price || '';
            document.getElementById('orderStopLoss').value = order.stop_loss || '';
        }
    }
    
    // Store the order ID for updates
    if (!document.getElementById('orderIdHidden')) {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = 'orderIdHidden';
        hiddenInput.name = 'order_id';
        document.getElementById('gttOrderForm').appendChild(hiddenInput);
    }
    document.getElementById('orderIdHidden').value = order.id || '';
    
    // Show the modal
    const modalElement = document.getElementById('gttOrderModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

// Function to toggle trigger fields based on trigger type
function toggleTriggerFields(triggerType = null) {
    // If no trigger type provided, get it from the dropdown
    if (!triggerType) {
        const triggerTypeSelect = document.getElementById('orderTriggerTypeDisplay');
        triggerType = triggerTypeSelect ? triggerTypeSelect.value : 'single';
    }
    
    // Get the order type to determine field visibility
    const orderType = document.getElementById('orderType').value;
    const triggerTypeDropdown = document.getElementById('orderTriggerTypeDisplay');
    
    // Hide trigger type dropdown for BUY orders (always single leg)
    if (orderType === 'BUY') {
        if (triggerTypeDropdown) {
            triggerTypeDropdown.closest('.col-md-4').style.display = 'none';
        }
        triggerType = 'single'; // Force single leg for BUY orders
    } else {
        // Show trigger type dropdown for SELL orders
        if (triggerTypeDropdown) {
            triggerTypeDropdown.closest('.col-md-4').style.display = 'block';
        }
    }
    
    const singleFields = document.getElementById('singleTriggerFields');
    const twoLegFields = document.getElementById('twoLegTriggerFields');
    
    if (triggerType === 'two-leg' && orderType === 'SELL') {
        // Show two-leg fields, hide single fields (only for SELL orders)
        if (singleFields) singleFields.style.display = 'none';
        if (twoLegFields) twoLegFields.style.display = 'block';
        
        // Clear single field values when switching to two-leg
        const triggerPriceField = document.getElementById('orderTriggerPrice');
        if (triggerPriceField) triggerPriceField.value = '';
        
        // Update field labels for SELL two-leg
        const targetLabel = document.querySelector('label[for="orderTargetPrice"]');
        const stopLossLabel = document.querySelector('label[for="orderStopLoss"]');
        if (targetLabel) targetLabel.textContent = 'Target Price (Profit Booking)';
        if (stopLossLabel) stopLossLabel.textContent = 'Stop Loss Price (Loss Cutting)';
        
    } else {
        // Show single fields, hide two-leg fields
        if (singleFields) singleFields.style.display = 'block';
        if (twoLegFields) twoLegFields.style.display = 'none';
        
        // Clear two-leg field values when switching to single
        const targetPriceField = document.getElementById('orderTargetPrice');
        const stopLossField = document.getElementById('orderStopLoss');
        if (targetPriceField) targetPriceField.value = '';
        if (stopLossField) stopLossField.value = '';
        
        // Update trigger price label based on order type
        const triggerLabel = document.querySelector('label[for="orderTriggerPrice"]');
        if (triggerLabel) {
            if (orderType === 'BUY') {
                triggerLabel.textContent = 'Trigger Price (Buy when price drops to)';
            } else {
                triggerLabel.textContent = 'Trigger Price (Sell when price reaches)';
            }
        }
    }
    
    // Update the hidden trigger type field
    const hiddenTriggerType = document.getElementById('orderTriggerType');
    if (hiddenTriggerType) {
        hiddenTriggerType.value = triggerType;
    }
    
    console.log('Toggled trigger fields to:', triggerType, 'for order type:', orderType);
}

// Global functions
window.openTradingViewPopup = openTradingViewPopup;
window.toggleQuery = toggleQuery;
