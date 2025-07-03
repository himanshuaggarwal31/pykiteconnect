// Dashboard GTT Orders - Main JavaScript

// Global variables for filtering and calculations
let allRows = [];
let filteredRows = [];
let currentRowLimit = 25;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - initializing dashboard');
    
    // Initialize the dashboard
    initializeDashboard();
    
    // Set up event listeners
    setupEventListeners();
    
    // Try calculating totals with multiple attempts
    attemptCalculation();
});

function attemptCalculation() {
    // Try immediate calculation
    calculateOrderTotals();
    
    // Try again after delays to handle dynamic content
    setTimeout(calculateOrderTotals, 100);
    setTimeout(calculateOrderTotals, 500);
    setTimeout(calculateOrderTotals, 1500);
}

function initializeDashboard() {
    console.log('=== initializeDashboard called ===');
    
    // Store all table rows for filtering
    const tableBody = document.querySelector('#ordersTable tbody');
    console.log('tableBody found:', !!tableBody);
    
    if (tableBody) {
        allRows = Array.from(tableBody.querySelectorAll('tr'));
        filteredRows = [...allRows];
        console.log('allRows initialized:', allRows.length);
        console.log('filteredRows initialized:', filteredRows.length);
    } else {
        console.warn('Table body not found during initialization');
        // Try alternative selector
        const altTable = document.getElementById('ordersTable');
        console.log('Alternative table found:', !!altTable);
        if (altTable) {
            const altBody = altTable.querySelector('tbody');
            console.log('Alternative tbody found:', !!altBody);
            if (altBody) {
                allRows = Array.from(altBody.querySelectorAll('tr'));
                filteredRows = [...allRows];
                console.log('allRows from alternative:', allRows.length);
            }
        }
        
        if (allRows.length === 0) {
            console.warn('No rows found, will retry in calculateAndUpdateTotals');
            return;
        }
    }
    
    // Apply initial row limit
    applyRowLimit();
    
    // Apply saved table density
    const savedDensity = localStorage.getItem('tableDensity') || 'compact';
    setTableDensity(savedDensity);
}

function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('dashboardSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
    
    // Filter dropdowns
    const transactionFilter = document.getElementById('transactionFilter');
    const statusFilter = document.getElementById('statusFilter');
    const exchangeFilter = document.getElementById('exchangeFilter');
    
    if (transactionFilter) {
        transactionFilter.addEventListener('change', applyFilters);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    if (exchangeFilter) {
        exchangeFilter.addEventListener('change', applyFilters);
    }
    
    // Row limit selector
    const lengthSelect = document.getElementById('dashboardLength');
    if (lengthSelect) {
        lengthSelect.addEventListener('change', handleRowLimitChange);
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refreshTable');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshPage);
    }
}

function handleSearch() {
    const searchTerm = document.getElementById('dashboardSearch').value.toLowerCase().trim();
    
    if (!searchTerm) {
        // If no search term, show all rows (respecting other filters)
        applyFilters();
        return;
    }
    
    // Filter rows based on search term
    filteredRows = allRows.filter(row => {
        const text = row.textContent.toLowerCase();
        return text.includes(searchTerm);
    });
    
    applyCurrentFilters();
    updateTableDisplay();
}

function applyFilters() {
    const transactionValue = document.getElementById('transactionFilter').value;
    const statusValue = document.getElementById('statusFilter').value;
    const exchangeValue = document.getElementById('exchangeFilter').value;
    
    // Start with all rows
    filteredRows = [...allRows];
    
    // Apply search if exists
    const searchTerm = document.getElementById('dashboardSearch').value.toLowerCase().trim();
    if (searchTerm) {
        filteredRows = filteredRows.filter(row => {
            const text = row.textContent.toLowerCase();
            return text.includes(searchTerm);
        });
    }
    
    // Apply transaction filter
    if (transactionValue) {
        filteredRows = filteredRows.filter(row => {
            const transaction = row.dataset.transaction;
            return transaction === transactionValue;
        });
    }
    
    // Apply status filter
    if (statusValue) {
        filteredRows = filteredRows.filter(row => {
            const status = row.dataset.status;
            return status === statusValue;
        });
    }
    
    // Apply exchange filter
    if (exchangeValue) {
        filteredRows = filteredRows.filter(row => {
            const exchange = row.dataset.exchange;
            return exchange === exchangeValue;
        });
    }
    
    updateTableDisplay();
    calculateOrderTotals();
}

function applyCurrentFilters() {
    // Re-apply current filter values to the already filtered results
    const transactionValue = document.getElementById('transactionFilter').value;
    const statusValue = document.getElementById('statusFilter').value;
    const exchangeValue = document.getElementById('exchangeFilter').value;
    
    if (transactionValue) {
        filteredRows = filteredRows.filter(row => {
            const transaction = row.dataset.transaction;
            return transaction === transactionValue;
        });
    }
    
    if (statusValue) {
        filteredRows = filteredRows.filter(row => {
            const status = row.dataset.status;
            return status === statusValue;
        });
    }
    
    if (exchangeValue) {
        filteredRows = filteredRows.filter(row => {
            const exchange = row.dataset.exchange;
            return exchange === exchangeValue;
        });
    }
}

function updateTableDisplay() {
    // Hide all rows first
    allRows.forEach(row => {
        row.style.display = 'none';
    });
    
    // Show filtered rows up to the limit
    const limit = currentRowLimit === -1 ? filteredRows.length : Math.min(currentRowLimit, filteredRows.length);
    
    for (let i = 0; i < limit; i++) {
        if (filteredRows[i]) {
            filteredRows[i].style.display = '';
        }
    }
    
    // Update row count display if needed
    updateRowCountDisplay();
    
    // Recalculate totals after updating display
    calculateOrderTotals();
}

function handleRowLimitChange() {
    const select = document.getElementById('dashboardLength');
    currentRowLimit = parseInt(select.value);
    
    updateTableDisplay();
}

function updateRowCountDisplay() {
    // Add row count info if element exists
    const countElement = document.getElementById('rowCountDisplay');
    if (countElement) {
        const showing = currentRowLimit === -1 ? filteredRows.length : Math.min(currentRowLimit, filteredRows.length);
        countElement.textContent = `Showing ${showing} of ${filteredRows.length} entries (${allRows.length} total)`;
    }
}

function applyRowLimit() {
    const select = document.getElementById('dashboardLength');
    if (select) {
        currentRowLimit = parseInt(select.value);
    }
    updateTableDisplay();
}

// Fresh implementation of order totals calculation
function calculateOrderTotals() {
    // Initialize totals
    const totals = {
        buy: 0,
        sell: 0,
        count: {
            total: 0,
            visible: 0,
            buy: 0,
            sell: 0
        }
    };
    
    // Get the orders table
    const ordersTable = document.getElementById('ordersTable');
    if (!ordersTable) {
        updateTotalsDisplay(totals);
        return;
    }
    
    // Get all order rows in the table body
    const orderRows = ordersTable.querySelectorAll('tbody tr');
    totals.count.total = orderRows.length;
    
    // If no rows found, just update display and return
    if (orderRows.length === 0) {
        updateTotalsDisplay(totals);
        return;
    }
    
    // Process each visible order row
    orderRows.forEach((row) => {
        // Skip hidden rows (filtered out)
        if (row.style.display === 'none') {
            return;
        }
        
        totals.count.visible++;
        
        // Extract order data from the row
        const orderData = extractOrderDataFromRow(row);
        if (!orderData) {
            return;
        }
        
        // Add to appropriate totals
        if (orderData.transaction === 'BUY') {
            totals.buy += orderData.amount;
            totals.count.buy++;
        } else if (orderData.transaction === 'SELL') {
            totals.sell += orderData.amount;
            totals.count.sell++;
        }
    });
    
    // Update the display
    updateTotalsDisplay(totals);
}

// Extract order data from a table row
function extractOrderDataFromRow(row) {
    try {
        // Get transaction type from data attribute
        const transaction = row.getAttribute('data-transaction');
        if (!transaction) {
            return null;
        }
        
        // Get the amount cell (8th column)
        const amountCell = row.querySelector('td:nth-child(8)');
        if (!amountCell) {
            return null;
        }
        
        // Try to get amount from data attribute first
        let amount = 0;
        const dataAmount = amountCell.getAttribute('data-amount');
        if (dataAmount) {
            amount = parseFloat(dataAmount);
        } else {
            // Fallback: parse from cell text content
            const cellText = amountCell.textContent.replace(/[₹,\s]/g, '');
            amount = parseFloat(cellText);
        }
        
        // Validate amount
        if (isNaN(amount) || amount <= 0) {
            return null;
        }
        
        return {
            transaction: transaction.toUpperCase(),
            amount: amount
        };
        
    } catch (error) {
        console.warn('Error extracting order data from row:', error);
        return null;
    }
}

// Update the totals display in the UI
function updateTotalsDisplay(totals) {
    // Update individual amounts
    const buyElement = document.getElementById('totalBuyAmount');
    const sellElement = document.getElementById('totalSellAmount');
    const netElement = document.getElementById('netAmount');
    const countElement = document.getElementById('orderCountDisplay');
    
    if (buyElement) {
        buyElement.textContent = formatCurrencyAmount(totals.buy);
    }
    
    if (sellElement) {
        sellElement.textContent = formatCurrencyAmount(totals.sell);
    }
    
    if (netElement) {
        const netAmount = totals.buy - totals.sell;
        netElement.textContent = formatCurrencyAmount(Math.abs(netAmount));
        
        // Update color based on net position
        const netContainer = netElement.closest('.net-total strong');
        if (netContainer) {
            netContainer.className = netAmount >= 0 ? 'text-success' : 'text-danger';
        }
    }
    
    if (countElement) {
        const countText = `Showing ${totals.count.visible} of ${totals.count.total} orders`;
        const breakdownText = totals.count.visible > 0 
            ? ` (${totals.count.buy} BUY, ${totals.count.sell} SELL)`
            : '';
        countElement.textContent = countText + breakdownText;
    }
}

// Format currency amount with Indian number formatting
function formatCurrencyAmount(amount) {
    return new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount || 0);
}

function refreshPage() {
    location.reload();
}

// Table density control
function setTableDensity(density) {
    const table = document.getElementById('ordersTable');
    if (!table) return;
    
    table.classList.remove('table-compact', 'table-normal');
    table.classList.add(density === 'compact' ? 'table-compact' : 'table-normal');
    
    localStorage.setItem('tableDensity', density);
    updateDensityButtons(density);
}

function updateDensityButtons(density) {
    const compactBtn = document.getElementById('compactView');
    const normalBtn = document.getElementById('normalView');
    
    if (compactBtn) {
        compactBtn.classList.toggle('active', density === 'compact');
    }
    if (normalBtn) {
        normalBtn.classList.toggle('active', density === 'normal');
    }
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Modal and order management functions
function createOrder() {
    const form = document.getElementById('createOrderForm');
    if (!form) {
        console.error('Create order form not found');
        return;
    }
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Remove amount_to_invest from payload (not needed by backend)
    delete data.amount_to_invest;
    
    fetch('/api/gtt/order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                throw new Error(`Expected JSON response but received: ${text.substring(0, 100)}...`);
            });
        }
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Create Order Error:', error);
        alert('Error creating order: ' + error.message);
    });
}

function deleteOrder(orderId) {
    if (confirm('Are you sure you want to delete this order?')) {
        fetch(`/api/gtt/order/${orderId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                return response.text().then(text => {
                    throw new Error(`Expected JSON response but received: ${text.substring(0, 100)}...`);
                });
            }
        })
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Delete Order Error:', error);
            alert('Error deleting order: ' + error.message);
        });
    }
}

function createMultiGttOrders() {
    const form = document.getElementById('multiGttForm');
    if (!form) {
        console.error('Multi GTT form not found');
        return;
    }
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Parse orders_json as JSON
    try {
        data.orders_json = JSON.parse(data.orders_json);
    } catch (e) {
        return alert('Invalid JSON in orders_json field');
    }
    
    fetch('/api/gtt/orders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                throw new Error(`Expected JSON response but received: ${text.substring(0, 100)}...`);
            });
        }
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Multi GTT Orders Error:', error);
        alert('Error creating multi GTT orders: ' + error.message);
    });
}

// Quantity/Amount calculation for create order modal
document.addEventListener('DOMContentLoaded', function() {
    setupOrderFormCalculations();
});

function setupOrderFormCalculations() {
    const amountInput = document.getElementById('amountToInvestInput');
    const triggerValuesInput = document.getElementById('triggerValuesInput');
    const quantityInput = document.getElementById('quantityInput');
    
    if (!amountInput || !triggerValuesInput || !quantityInput) {
        return; // Elements not found, probably not on the right page
    }
    
    function getFirstTriggerValue() {
        const val = triggerValuesInput.value.split(',')[0].trim();
        return parseFloat(val) || 0;
    }
    
    function updateQuantityFromAmount() {
        const amount = parseFloat(amountInput.value) || 0;
        const price = getFirstTriggerValue();
        if (amount > 0 && price > 0) {
            quantityInput.value = Math.floor(amount / price);
        }
    }
    
    function updateAmountFromQuantity() {
        const qty = parseFloat(quantityInput.value) || 0;
        const price = getFirstTriggerValue();
        if (qty > 0 && price > 0) {
            amountInput.value = (qty * price).toFixed(2);
        }
    }
    
    amountInput.addEventListener('input', updateQuantityFromAmount);
    triggerValuesInput.addEventListener('input', function() {
        updateQuantityFromAmount();
        updateAmountFromQuantity();
    });
    quantityInput.addEventListener('input', updateAmountFromQuantity);
}

// Export functions to global scope
window.setTableDensity = setTableDensity;
window.createOrder = createOrder;
window.deleteOrder = deleteOrder;
window.createMultiGttOrders = createMultiGttOrders;

// Test the filtering functionality
function testFilters() {
    console.log('Testing filters...');
    
    // Test search
    const searchInput = document.getElementById('dashboardSearch');
    if (searchInput) {
        searchInput.value = 'KPIT';
        handleSearch();
        console.log('Search test completed');
    }
    
    // Test transaction filter
    const transactionFilter = document.getElementById('transactionFilter');
    if (transactionFilter) {
        transactionFilter.value = 'BUY';
        applyFilters();
        console.log('Transaction filter test completed');
    }
}

// Add test function to global scope
window.testFilters = testFilters;
