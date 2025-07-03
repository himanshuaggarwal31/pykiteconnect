/**
 * Custom GTT Orders Management
 * Handles saving, editing, and placing GTT orders
 */

// Global error handler to catch any unexpected JavaScript errors
window.addEventListener('error', function(event) {
    console.error('Global JavaScript error caught:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
    
    // Show user-friendly error message for critical errors
    if (event.message && event.message.includes('Cannot read properties of undefined')) {
        console.warn('Detected undefined property access error');
        // Don't show toast for these as they can be very noisy
    }
});

// Global promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    // Prevent the error from showing in the console as uncaught
    event.preventDefault();
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOMContentLoaded fired - Starting initialization');
    
    // Wait a bit for all elements to be ready
    setTimeout(function() {
        console.log('🔧 Starting delayed initialization');
        
        // Initialize any missing elements first
        initializeMissingElements();
        
        // Add ID to table body for easier selection
        const tableBody = document.querySelector('#customGttTable tbody');
        if (tableBody && !tableBody.id) {
            tableBody.id = 'customGttTableBody';
            console.log('✅ Added ID to table body element');
        }
        
        // Verify critical elements exist
        const table = document.getElementById('customGttTable');
        const tbody = document.getElementById('customGttTableBody');
        const searchInput = document.getElementById('searchInput');
        
        console.log('🔍 Element check:', {
            table: !!table,
            tbody: !!tbody,
            searchInput: !!searchInput
        });
        
        if (!table || !tbody) {
            console.error('❌ Critical table elements missing! Retrying in 1 second...');
            setTimeout(initializeGTTPage, 1000);
            return;
        }
        
        console.log('✅ Custom GTT Orders page initialized');
        
        // Add event listeners for price and quantity fields to update amount
        const priceElements = ['lastPrice', 'quantity', 'triggerPrice', 'targetPrice', 'stopLoss'];
        priceElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', updateOrderAmount);
                console.log(`✅ Added input listener to ${id} element`);
            }
        });
        
        // Add event listener for trigger type change to toggle fields
        const triggerTypeElement = document.getElementById('triggerType');
        if (triggerTypeElement) {
            triggerTypeElement.addEventListener('change', function() {
                console.log('Trigger type changed to:', this.value);
                toggleTriggerFields(this.value);
                updateOrderAmount(); // Recalculate amount when switching types
            });
            console.log('✅ Added change listener to triggerType element');
        }
        
        // Initialize modal
        const orderModal = document.getElementById('orderModal');
        if (orderModal) {
            console.log('✅ Initializing orderModal');
            const bsOrderModal = new bootstrap.Modal(orderModal);
            
            // Make sure the modal is properly hidden when closed
            orderModal.addEventListener('hidden.bs.modal', function() {
                console.log('Modal hidden event');
                const form = document.getElementById('orderForm');
                if (form) form.reset();
            });
        } else {
            console.warn('⚠️ Order modal element not found!');
        }
        
        // Initialize search functionality with proper error handling
        console.log('🔍 Initializing search functionality...');
        try {
            const fetchTableData = initializeSearch({
                searchInputId: 'searchInput',
                tableId: 'customGttTable',
                fetchUrl: '/api/custom-gtt/orders',
                updateCallback: updateOrdersTable,
                additionalParams: {
                    order_type: () => document.getElementById('orderTypeFilter')?.value || '',
                    kite_status: () => document.getElementById('kiteStatusFilter')?.value || ''
                }
            });
            
            console.log('✅ Search initialization completed');
            
            // Store fetchTableData globally for debugging
            window.debugFetchTableData = fetchTableData;
            
        } catch (error) {
            console.error('❌ Search initialization failed:', error);
            
            // Fallback: manual initial load
            console.log('🔄 Attempting manual fallback load...');
            setTimeout(() => {
                fetch('/api/custom-gtt/orders')
                    .then(response => response.json())
                    .then(data => {
                        console.log('✅ Fallback data fetch successful:', data);
                        updateOrdersTable(data);
                    })
                    .catch(error => {
                        console.error('❌ Fallback fetch failed:', error);
                    });
            }, 500);
        }
        
        // Initialize select all checkbox
        const selectAllCheckbox = document.getElementById('selectAllOrders');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('.order-select:not(:disabled)');
                checkboxes.forEach(checkbox => checkbox.checked = this.checked);
                updateSelectedCount();
                updateTotalAmount();
            });
            console.log('✅ Initialized table header select all checkbox');
        }
        
        // Also handle the main select all checkbox
        const selectAllMainCheckbox = document.getElementById('selectAllOrdersMain');
        if (selectAllMainCheckbox) {
            selectAllMainCheckbox.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('.order-select:not(:disabled)');
                checkboxes.forEach(checkbox => checkbox.checked = this.checked);
                updateSelectedCount();
                updateTotalAmount();
                
                // Sync with the table header checkbox
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = this.checked;
                }
            });
            console.log('✅ Initialized main select all checkbox');
        }
        
        // Initialize filter handlers
        ['orderTypeFilter', 'kiteStatusFilter', 'recordsPerPage'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', window.debugFetchTableData || function() {
                    console.log('Filter changed but fetchTableData not available');
                });
                console.log(`✅ Added change listener to ${id}`);
            }
        });
        
        // Initialize pagination buttons
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                const currentPageEl = document.getElementById('currentPage');
                if (currentPageEl) {
                    const currentPage = parseInt(currentPageEl.textContent) || 1;
                    if (currentPage > 1) {
                        currentPageEl.textContent = currentPage - 1;
                        if (window.debugFetchTableData) {
                            window.debugFetchTableData();
                        }
                    }
                }
            });
            console.log('✅ Initialized prev page button');
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const currentPageEl = document.getElementById('currentPage');
                const totalPagesEl = document.getElementById('totalPages');
                if (currentPageEl && totalPagesEl) {
                    const currentPage = parseInt(currentPageEl.textContent) || 1;
                    const totalPages = parseInt(totalPagesEl.textContent) || 1;
                    if (currentPage < totalPages) {
                        currentPageEl.textContent = currentPage + 1;
                        if (window.debugFetchTableData) {
                            window.debugFetchTableData();
                        }
                    }
                }
            });
            console.log('✅ Initialized next page button');
        }
        
        // Initialize sorting functionality
        initializeSorting();
        
    }, 100); // Small delay to ensure DOM is fully ready
    
    // Make debug function globally available (no floating button)
    window.performTableDebug = performTableDebug;
    
});

// Global variables for sorting
let currentSortColumn = null;
let currentSortDirection = 'asc';

/**
 * Updates the orders table with data from the API
 */
function updateOrdersTable(data) {
    console.log('=== updateOrdersTable CALLED ===');
    console.log('Input data:', data);
    console.log('Data type:', typeof data);
    console.log('Data keys:', data ? Object.keys(data) : 'null/undefined');
    
    // Safety check for data parameter
    if (!data || typeof data !== 'object') {
        console.error('Invalid data provided to updateOrdersTable:', data);
        return;
    }
    
    // Try multiple selectors to find the table body
    let tbody = document.getElementById('customGttTableBody');
    if (!tbody) {
        tbody = document.querySelector('#customGttTable tbody');
        console.log('Using querySelector to find table body');
    }
    
    if (!tbody) {
        console.error('Table body element not found! Make sure the table structure is correct.');
        console.log('Table element exists:', !!document.getElementById('customGttTable'));
        
        // Let's check what table elements exist
        const allTables = document.querySelectorAll('table');
        console.log('All tables found:', allTables.length);
        allTables.forEach((table, index) => {
            console.log(`Table ${index}:`, table.id, table.className);
        });
        
        return;
    }
    
    console.log('Table body found:', tbody);
    console.log('Current tbody innerHTML length:', tbody.innerHTML.length);
    
    // Clear existing content
    tbody.innerHTML = '';
    console.log('Cleared tbody content');
    
    if (!data.records || !Array.isArray(data.records) || data.records.length === 0) {
        console.log('No records found, showing empty state');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td colspan="13" class="text-center py-3">
                <i class="fas fa-info-circle me-2"></i>No orders found. Add a new order to get started.
            </td>
        `;
        tbody.appendChild(tr);
        console.log('Added empty state row');
        
        // Update UI counts with safety checks
        safeSetTextContent('totalAmount', '0.00');
        safeSetTextContent('totalAllAmount', '0.00');
        safeSetTextContent('currentRecords', '0');
        safeSetTextContent('totalRecords', '0');
        safeSetTextContent('currentPage', '1');
        safeSetTextContent('totalPages', '1');
        safeSetTextContent('selectedCount', '0');
        
        // Disable pagination
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        if (prevBtn) prevBtn.disabled = true;
        if (nextBtn) nextBtn.disabled = true;
        
        console.log('Updated UI for empty state');
        return;
    }
    
    console.log(`Processing ${data.records.length} records`);
    
    data.records.forEach((order, index) => {
        console.log(`Processing order ${index}:`, order);
        
        // Safety check for order object
        if (!order || typeof order !== 'object') {
            console.warn('Skipping invalid order object:', order);
            return;
        }
        
        const tr = document.createElement('tr');
        tr.dataset.id = order.id || '';
        console.log(`Created row for order ID: ${order.id}`);
        
        // Format trigger values with safety checks
        let triggerValuesDisplay = '';
        if (order.trigger_type === 'two-leg' && order.trigger_values) {
            try {
                const values = String(order.trigger_values).split(',').map(v => parseFloat(v));
                if (values.length === 2 && !isNaN(values[0]) && !isNaN(values[1])) {
                    triggerValuesDisplay = `SL: ${values[0]}, Target: ${values[1]}`;
                } else {
                    triggerValuesDisplay = order.trigger_values;
                }
            } catch (e) {
                console.warn('Error parsing trigger values:', e);
                triggerValuesDisplay = order.trigger_values || '';
            }
        } else if (order.trigger_price) {
            triggerValuesDisplay = order.trigger_price;
        }
        
        // Calculate amount with safety checks
        const amount = calculateAmount(order);
        const amountDisplay = formatCurrency(amount);
        
        // Status badge with safety check
        const statusBadge = order.placed_on_kite ? 
            `<span class="badge bg-success">Placed</span>` :
            `<span class="badge bg-secondary">Saved</span>`;
        
        // Action buttons with safety checks
        let actionButtons = '';
        if (!order.placed_on_kite) {
            actionButtons = `
                <button class="btn btn-sm btn-success action-btn" onclick="placeOrder(${order.id || 0})" title="Place on Kite">
                    <i class="fas fa-upload"></i> Place
                </button>
                <button class="btn btn-sm btn-primary action-btn ms-1" onclick="editOrder(${order.id || 0})" title="Edit">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger action-btn ms-1" onclick="deleteOrder(${order.id || 0})" title="Delete">
                    <i class="fas fa-trash"></i> Delete
                </button>
            `;
        } else {
            actionButtons = `
                <button class="btn btn-sm btn-warning action-btn" onclick="resetOrder(${order.id || 0})" title="Reset Status">
                    <i class="fas fa-undo"></i> Reset
                </button>
                <button class="btn btn-sm btn-danger action-btn ms-1" onclick="deleteOrder(${order.id || 0})" title="Delete">
                    <i class="fas fa-trash"></i> Delete
                </button>
            `;
        }
        
        tr.innerHTML = `
            <td><input type="checkbox" class="order-select" value="${order.id || ''}" ${order.placed_on_kite ? 'disabled' : ''} onchange="handleCheckboxChange()"></td>
            <td>${order.symbol || 'N/A'}</td>
            <td class="company-column">${order.company_name ? `<span title="${order.company_name}">${order.company_name.length > 25 ? order.company_name.substring(0, 25) + '...' : order.company_name}</span>` : ''}</td>
            <td>${order.exchange || 'NSE'}</td>
            <td>${order.order_type || 'N/A'}</td>
            <td>${triggerValuesDisplay}</td>
            <td>${order.last_price || 'N/A'}</td>
            <td>${order.quantity || 0}</td>
            <td class="text-end">${amountDisplay}</td>
            <td class="text-center">${order.nifty_rank ? order.nifty_rank : '<span class="text-muted">-</span>'}</td>
            <td class="notes-column">${order.notes ? `<span title="${order.notes}">${order.notes.length > 20 ? order.notes.substring(0, 20) + '...' : order.notes}</span>` : ''}</td>
            <td>${statusBadge}</td>
            <td class="action-buttons">${actionButtons}</td>
        `;
        
        tbody.appendChild(tr);
        console.log(`Added row for order ${order.id} to tbody`);
    });
    
    console.log(`Finished adding ${data.records.length} rows to table`);
    console.log('Final tbody innerHTML length:', tbody.innerHTML.length);
    console.log('Final tbody children count:', tbody.children.length);
    
    // Update UI counts and pagination with safety checks
    safeSetTextContent('currentRecords', data.records ? data.records.length : 0);
    safeSetTextContent('totalRecords', data.total_count || 0);
    safeSetTextContent('currentPage', data.page || 1);
    safeSetTextContent('totalPages', data.pages || 1);
    
    console.log('Updated UI counts');
    
    // Enable/disable pagination buttons with safety checks
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    
    if (prevBtn) prevBtn.disabled = ((data.page || 1) <= 1);
    if (nextBtn) nextBtn.disabled = ((data.page || 1) >= (data.pages || 1));
    
    // Update total amount
    updateTotalAmount();
    updateTotalAllAmount();
    updateSelectedCount();
}

/**
 * Navigate to a specific page
 */
function navigateToPage(page) {
    const searchInput = document.getElementById('searchInput');
    const orderTypeFilter = document.getElementById('orderTypeFilter');
    const kiteStatusFilter = document.getElementById('kiteStatusFilter');
    const recordsPerPage = document.getElementById('recordsPerPage');
    
    const params = new URLSearchParams({
        page: page,
        per_page: recordsPerPage.value
    });
    
    if (searchInput.value) {
        params.append('search', searchInput.value);
    }
    
    if (orderTypeFilter.value) {
        params.append('order_type', orderTypeFilter.value);
    }
    
    if (kiteStatusFilter.value) {
        params.append('kite_status', kiteStatusFilter.value);
    }
    
    fetch(`/api/custom-gtt/orders?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            updateOrdersTable(data);
        })
        .catch(error => {
            console.error('Error navigating to page:', error);
            showToast('Failed to navigate to page', 'error');
        });
}

/**
 * Calculate the amount for an order
 */
function calculateAmount(order) {
    // Safety check for order object
    if (!order || typeof order !== 'object') {
        return 0;
    }
    
    const quantity = parseInt(order.quantity) || 0;
    let price = 0;
    
    if (order.last_price) {
        const parsedPrice = parseFloat(order.last_price);
        if (!isNaN(parsedPrice)) price = parsedPrice;
    } else if (order.trigger_price) {
        const parsedPrice = parseFloat(order.trigger_price);
        if (!isNaN(parsedPrice)) price = parsedPrice;
    } else if (order.trigger_values) {
        try {
            const values = String(order.trigger_values).split(',');
            if (values.length > 0) {
                const parsedPrice = parseFloat(values[0]);
                if (!isNaN(parsedPrice)) price = parsedPrice;
            }
        } catch (e) {
            console.warn('Error parsing trigger values for amount calculation:', e);
        }
    }
    
    return quantity * price;
}

/**
 * Update the total amount display
 */
function updateTotalAmount() {
    let total = 0;
    const rows = document.querySelectorAll('#customGttTableBody tr[data-id]');
    
    rows.forEach(row => {
        const checkbox = row.querySelector('.order-select');
        if (checkbox && checkbox.checked) {
            const amountCell = row.cells[8]; // Amount column (0-based index)
            if (amountCell) {
                const amount = parseFloat(amountCell.textContent.replace(/[^0-9.-]+/g, '')) || 0;
                total += amount;
            }
        }
    });
    
    safeSetTextContent('totalAmount', formatCurrency(total).replace('₹', ''));
}

/**
 * Update the total amount of all orders (not just selected)
 */
function updateTotalAllAmount() {
    let total = 0;
    const rows = document.querySelectorAll('#customGttTableBody tr[data-id]');
    
    rows.forEach(row => {
        const amountCell = row.cells[8]; // Amount column (0-based index)
        if (amountCell) {
            const amount = parseFloat(amountCell.textContent.replace(/[^0-9.-]+/g, '')) || 0;
            total += amount;
        }
    });
    
    safeSetTextContent('totalAllAmount', formatCurrency(total).replace('₹', ''));
}

/**
 * Update the selected count display
 */
function updateSelectedCount() {
    const selectedCheckboxes = document.querySelectorAll('.order-select:checked');
    safeSetTextContent('selectedCount', selectedCheckboxes.length);
}

/**
 * Format currency amount
 */
function formatCurrency(amount) {
    // Safety check for amount
    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount)) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(0);
    }
    
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(parsedAmount);
}

/**
 * Handle checkbox change
 */
function handleCheckboxChange() {
    updateSelectedCount();
    updateTotalAmount();
}

/**
 * Get selected order IDs
 */
function getSelectedOrders() {
    const selectedOrders = [];
    const checkboxes = document.querySelectorAll('.order-select:checked');
    
    checkboxes.forEach(checkbox => {
        selectedOrders.push(parseInt(checkbox.value));
    });
    
    return selectedOrders;
}

/**
 * Show order modal for add/edit
 */
function showOrderModal(orderId = null) {
    console.log('Showing order modal for ID:', orderId);
    
    // Check if Bootstrap is loaded
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not defined! Make sure Bootstrap JS is loaded.');
        
        // Check if jQuery and jQuery UI are available as fallbacks
        if (typeof $ !== 'undefined' || typeof jQuery !== 'undefined') {
            console.log('jQuery is available but Bootstrap is not');
            if (typeof ($ || jQuery).fn.modal === 'function') {
                console.log('jQuery modal function is available');
            }
        }
        
        console.error('Bootstrap object missing. Logging loaded scripts:');
        document.querySelectorAll('script').forEach(s => console.log('Script:', s.src));
        alert('Error: Bootstrap JS is not loaded. Please reload the page and try again.');
        return;
    }
    
    console.log('Bootstrap version check:', bootstrap.Modal ? 'Modal class exists' : 'Modal class missing');
    
    // Get modal DOM element
    const modalElement = document.getElementById('orderModal');
    if (!modalElement) {
        console.error('Modal element not found!');
        // List all modals in the page to help debug
        const allModals = document.querySelectorAll('.modal');
        console.log('Available modals on page:', allModals.length);
        allModals.forEach((m, i) => console.log(`Modal ${i}:`, m.id));
        return;
    }
    console.log('Modal element found:', modalElement);

    // Clear any existing modal
    try {
        let existingModal = bootstrap.Modal.getInstance(modalElement);
        if (existingModal) {
            console.log('Disposing existing modal instance');
            existingModal.dispose();
        }
    } catch (err) {
        console.error('Error disposing existing modal:', err);
    }
    
    // Reset form
    const form = document.getElementById('orderForm');
    if (form) {
        form.reset();
        console.log('Form reset successfully');
    } else {
        console.error('Order form not found!');
        // List all forms in the page to help debug
        const allForms = document.querySelectorAll('form');
        console.log('Available forms on page:', allForms.length);
        allForms.forEach((f, i) => console.log(`Form ${i}:`, f.id));
        return;
    }
    
    // Initialize modal
    let modal;
    try {
        console.log('Creating new Bootstrap modal instance');
        modal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: false
        });
        
        // Store modal instance for later reference
        window.currentOrderModal = modal;
        
        const modalTitle = document.getElementById('orderModalTitle');
        if (modalTitle) {
            console.log('Setting modal title');
            modalTitle.textContent = orderId ? 'Edit Order' : 'Add New Order';
        } else {
            console.error('Modal title element not found!');
            // Try to find the correct title element
            const possibleTitles = modalElement.querySelectorAll('.modal-title');
            console.log('Found modal title elements:', possibleTitles.length);
            if (possibleTitles.length > 0) {
                console.log('Using first found modal title element');
                possibleTitles[0].textContent = orderId ? 'Edit Order' : 'Add New Order';
            }
        }
        
        // Don't show modal here - we'll show it after data is populated for edit mode
        // or immediately for add mode in the conditional logic below
        
        // Verify modal instance is ready
        console.log('Modal instance created, ready for conditional logic');
    } catch (err) {
        console.error('Error creating modal:', err);
        return;
    }
    
    if (orderId) {
        // Edit mode - fetch order data first before showing modal
        console.log('Edit mode for order ID:', orderId);
        const modalTitle = document.getElementById('orderModalTitle');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Order';
        }
        document.getElementById('orderId').value = orderId;
        
        // Fetch order data
        fetch(`/api/custom-gtt/orders/${orderId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    showToast(data.error, 'error');
                    return;
                }
                
                const order = data.order;
                console.log('Order data fetched:', order);
                
                // Fill form with order data - with null checks
                const setFieldValue = (fieldId, value) => {
                    const field = document.getElementById(fieldId);
                    if (field) {
                        field.value = value || '';
                        console.log(`Set ${fieldId} = ${value || ''}`);
                    } else {
                        console.error(`Field ${fieldId} not found!`);
                    }
                };
                
                setFieldValue('symbol', order.symbol);
                setFieldValue('companyName', order.company_name);
                setFieldValue('exchange', order.exchange || 'NSE');
                setFieldValue('orderType', order.order_type || 'BUY');
                setFieldValue('triggerType', order.trigger_type || 'single');
                setFieldValue('lastPrice', order.last_price);
                setFieldValue('quantity', order.quantity);
                setFieldValue('notes', order.notes);
                setFieldValue('niftyRank', order.nifty_rank);
                
                // Handle trigger type fields
                const triggerType = order.trigger_type || 'single';
                toggleTriggerFields(triggerType);
                
                if (triggerType === 'single') {
                    setFieldValue('triggerPrice', order.trigger_price);
                } else if (triggerType === 'two-leg') {
                    setFieldValue('stopLoss', order.stop_loss);
                    setFieldValue('targetPrice', order.target_price);
                }
                
                // Update order amount
                updateOrderAmount();
                
                // Show modal after data is populated
                console.log('Showing modal with populated data');
                modal.show();
            })
            .catch(error => {
                console.error('Error fetching order:', error);
                showToast('Failed to fetch order data', 'error');
            });
    } else {
        // Add mode
        console.log('Add mode - new order');
        const modalTitle = document.getElementById('orderModalTitle');
        if (modalTitle) {
            modalTitle.textContent = 'Add New Order';
        }
        document.getElementById('orderId').value = '';
        document.getElementById('triggerType').value = 'single';
        document.getElementById('exchange').value = 'NSE';
        document.getElementById('orderType').value = 'BUY';
        
        // Show only single trigger fields
        toggleTriggerFields('single');
        
        // Show modal immediately for new orders
        modal.show();
    }
}

/**
 * Toggle trigger fields based on trigger type
 */
function toggleTriggerFields(triggerType) {
    const singleFields = document.getElementById('singleTriggerFields');
    const twoLegFields = document.getElementById('twoLegTriggerFields');
    
    if (triggerType === 'single') {
        singleFields.style.display = 'block';
        twoLegFields.style.display = 'none';
    } else if (triggerType === 'two-leg') {
        singleFields.style.display = 'none';
        twoLegFields.style.display = 'block';
    }
}

/**
 * Update the order amount based on form inputs
 */
function updateOrderAmount() {
    const quantity = parseInt(document.getElementById('quantity').value) || 0;
    const triggerType = document.getElementById('triggerType').value;
    let price = parseFloat(document.getElementById('lastPrice').value) || 0;
    
    if (triggerType === 'single') {
        const triggerPrice = parseFloat(document.getElementById('triggerPrice').value) || 0;
        if (triggerPrice > 0) {
            price = triggerPrice;
        }
    } else if (triggerType === 'two-leg') {
        // For two-leg, we'll use the stop-loss price for calculation
        const stopLoss = parseFloat(document.getElementById('stopLoss').value) || 0;
        if (stopLoss > 0) {
            price = stopLoss;
        }
    }
    
    const amount = quantity * price;
    // Format the amount with 2 decimal places
    const formattedAmount = new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
    
    // Update the amount display in the modal
    const amountElement = document.getElementById('orderAmount');
    if (amountElement) {
        amountElement.textContent = formattedAmount;
    } else {
        console.error('orderAmount element not found!');
    }
    
    console.log(`Updated order amount: ${formattedAmount} (${quantity} × ${price})`);
}

/**
 * Fetch last price for a symbol
 */
function fetchLastPrice() {
    const symbol = document.getElementById('symbol').value;
    const exchange = document.getElementById('exchange').value;
    
    if (!symbol) {
        showToast('Please enter a symbol', 'warning');
        return;
    }
    
    // Show loading
    document.getElementById('fetchPriceBtn').innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    document.getElementById('fetchPriceBtn').disabled = true;
    
    fetch(`/api/custom-gtt/get-latest-price/${symbol}?exchange=${exchange}`)
        .then(response => response.json())
        .then(data => {
            // Reset button
            document.getElementById('fetchPriceBtn').innerHTML = 'Fetch';
            document.getElementById('fetchPriceBtn').disabled = false;
            
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            document.getElementById('lastPrice').value = data.last_price;
            showToast(`Last price for ${symbol}: ${formatCurrency(data.last_price)}`, 'success');
            
            // Update order amount
            updateOrderAmount();
        })
        .catch(error => {
            // Reset button
            document.getElementById('fetchPriceBtn').innerHTML = 'Fetch';
            document.getElementById('fetchPriceBtn').disabled = false;
            
            console.error('Error fetching price:', error);
            showToast('Failed to fetch price', 'error');
        });
}

/**
 * Validate the order form
 */
function validateOrderForm() {
    const symbol = document.getElementById('symbol').value.trim();
    const orderType = document.getElementById('orderType').value;
    const triggerType = document.getElementById('triggerType').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    
    if (!symbol) {
        showToast('Symbol is required', 'warning');
        return false;
    }
    
    if (!quantity || quantity <= 0) {
        showToast('Quantity must be a positive number', 'warning');
        return false;
    }
    
    // Company name is optional - no validation needed
    
    if (triggerType === 'single') {
        const triggerPrice = parseFloat(document.getElementById('triggerPrice').value);
        if (!triggerPrice || triggerPrice <= 0) {
            showToast('Trigger price is required and must be positive', 'warning');
            return false;
        }
    } else if (triggerType === 'two-leg') {
        const stopLoss = parseFloat(document.getElementById('stopLoss').value);
        const targetPrice = parseFloat(document.getElementById('targetPrice').value);
        
        if (!stopLoss || stopLoss <= 0) {
            showToast('Stop loss is required and must be positive', 'warning');
            return false;
        }
        
        if (!targetPrice || targetPrice <= 0) {
            showToast('Target price is required and must be positive', 'warning');
            return false;
        }
        
        if (orderType === 'BUY') {
            showToast('Two-leg orders are only supported for SELL orders', 'warning');
            return false;
        }
        
        // For SELL orders, stop loss should be lower than target
        if (stopLoss >= targetPrice) {
            showToast('For SELL orders, stop loss must be lower than target price', 'warning');
            return false;
        }
    }
    
    return true;
}

/**
 * Save a new or updated order
 */
function saveOrder() {
    console.log('Save order function called');
    // Show loading
    document.getElementById('saveOrderBtn').innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
    document.getElementById('saveOrderBtn').disabled = true;
    
    try {
        if (!validateOrderForm()) {
            console.log('Form validation failed');
            document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
            document.getElementById('saveOrderBtn').disabled = false;
            return;
        }
        
        const form = document.getElementById('orderForm');
        if (!form) {
            console.error('Form not found!');
            showToast('Error: Form not found!', 'error');
            document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
            document.getElementById('saveOrderBtn').disabled = false;
            return;
        }
        
        let formData;
        try {
            formData = new FormData(form);
        } catch (formError) {
            console.error('Error creating FormData:', formError);
            showToast('Error: Could not read form data', 'error');
            document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
            document.getElementById('saveOrderBtn').disabled = false;
            return;
        }
        
        const orderId = document.getElementById('orderId').value;
        
        // Convert to JSON - skip empty values to make fields truly optional
        const data = {};
        try {
            formData.forEach((value, key) => {
                if (value !== null && value !== '') {
                    data[key] = value;
                }
                console.log(`Form field ${key} = ${value}`);
            });
            
            // Explicitly log notes field for debugging
            if (formData && typeof formData.get === 'function') {
                console.log('Notes field value:', formData.get('notes'));
            } else {
                console.warn('FormData.get method not available');
            }
        } catch (forEachError) {
            console.error('Error processing form data:', forEachError);
            showToast('Error: Could not process form data', 'error');
            document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
            document.getElementById('saveOrderBtn').disabled = false;
            return;
        }
        
        console.log('Form data prepared:', data);
        
        // Special handling for trigger values in two-leg orders
        if (data.trigger_type === 'two-leg' && data.stop_loss && data.target_price) {
            data.trigger_values = `${data.stop_loss},${data.target_price}`;
            console.log('Set trigger_values for two-leg order:', data.trigger_values);
        }
        
        // Calculate amount for logging
        const quantity = parseInt(data.quantity) || 0;
        let price = parseFloat(data.lastPrice) || 0;
        if (data.triggerType === 'single' && data.triggerPrice) {
            price = parseFloat(data.triggerPrice);
        }
        console.log(`Order amount: ${quantity * price} (${quantity} × ${price})`);
        
        const url = orderId ? 
            `/api/custom-gtt/update-order/${orderId}` : 
            `/api/custom-gtt/save-order`;
            
        console.log('Submitting to URL:', url);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('Response status:', response.status);
            
            // Safely log response headers
            try {
                if (response.headers && typeof response.headers.entries === 'function') {
                    console.log('Response headers:', [...response.headers.entries()]);
                } else {
                    console.log('Response headers: Not available or not iterable');
                }
            } catch (e) {
                console.log('Could not log response headers:', e.message);
            }
            
            if (!response.ok) {
                console.error('Server response not OK:', response.status, response.statusText);
                // Try to parse error response as JSON
                return response.json().then(errData => {
                    console.error('Error response data:', errData);
                    throw new Error(errData.error || `Server error! Status: ${response.status}`);
                }).catch(jsonErr => {
                    // If JSON parsing fails, throw the original error
                    throw new Error(`Server error! Status: ${response.status}, ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Server response:', data);
            // Reset button
            document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
            document.getElementById('saveOrderBtn').disabled = false;
            
            if (data.error) {
                console.error('Error in response:', data.error);
                showToast(data.error, 'error');
                return;
            }
            
            // Hide modal
            bootstrap.Modal.getInstance(document.getElementById('orderModal')).hide();
            
            // Show success message
            showToast(orderId ? 'Order updated successfully' : 'Order saved successfully', 'success');
            
            // Refresh table data
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                const event = new Event('input', { bubbles: true });
                searchInput.dispatchEvent(event);
            }
        })
        .catch(error => {
            // Reset button
            document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
            document.getElementById('saveOrderBtn').disabled = false;
            
            console.error('Error saving order:', error);
            showToast(`Failed to save order: ${error.message}`, 'error');
            
            // Additional debugging
            if (error.response) {
                error.response.json().then(errData => {
                    console.error('Error response data:', errData);
                }).catch(e => console.error('Could not parse error response as JSON'));
            }
        });
    } catch (e) {
        document.getElementById('saveOrderBtn').innerHTML = 'Save Order';
        document.getElementById('saveOrderBtn').disabled = false;
        console.error('Error in saveOrder function:', e);
        showToast('Error saving order: ' + e.message, 'error');
    }
}

/**
 * Edit an existing order
 */
function editOrder(orderId) {
    showOrderModal(orderId);
}

/**
 * Delete an order
 */
function deleteOrder(orderId) {
    showConfirmationModal(
        'Delete Order',
        'Are you sure you want to delete this order? This action cannot be undone.',
        () => {
            fetch(`/api/custom-gtt/delete-order/${orderId}`, {
                method: 'POST'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showToast(data.error, 'error');
                        return;
                    }
                    
                    showToast('Order deleted successfully', 'success');
                    
                    // Refresh table data
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        const event = new Event('input', { bubbles: true });
                        searchInput.dispatchEvent(event);
                    }
                })
                .catch(error => {
                    console.error('Error deleting order:', error);
                    showToast('Failed to delete order', 'error');
                });
        }
    );
}

/**
 * Place a single order on Kite
 */
function placeOrder(orderId) {
    showConfirmationModal(
        'Place Order on Kite',
        'Are you sure you want to place this order on Kite? This action cannot be undone.',
        () => {
            // Show loading
            const button = document.querySelector(`tr[data-id="${orderId}"] .btn-success`);
            if (button) {
                button.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
                button.disabled = true;
            }
            
            fetch(`/api/custom-gtt/place-order/${orderId}`, {
                method: 'POST'
            })
                .then(response => response.json())
                .then(data => {
                    // Reset button
                    if (button) {
                        button.innerHTML = '<i class="fas fa-upload"></i> Place';
                        button.disabled = false;
                    }
                    
                    if (data.error) {
                        showToast(data.error, 'error');
                        return;
                    }
                    
                    showToast(`Order placed on Kite with trigger ID: ${data.trigger_id}`, 'success');
                    
                    // Refresh table data
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        const event = new Event('input', { bubbles: true });
                        searchInput.dispatchEvent(event);
                    }
                })
                .catch(error => {
                    // Reset button
                    if (button) {
                        button.innerHTML = '<i class="fas fa-upload"></i> Place';
                        button.disabled = false;
                    }
                    
                    console.error('Error placing order:', error);
                    showToast('Failed to place order on Kite', 'error');
                });
        }
    );
}

/**
 * Place multiple orders on Kite
 */
function placeMultipleOrders(orderIds) {
    // Show loading
    const button = document.getElementById('placeAllOrdersBtn');
    button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Placing...';
    button.disabled = true;
    
    fetch('/api/custom-gtt/place-orders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ order_ids: orderIds })
    })
        .then(response => response.json())
        .then(data => {
            // Reset button
            button.innerHTML = '<i class="fas fa-upload me-1"></i>Place Selected Orders on Kite';
            button.disabled = false;
            
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            const successCount = data.results?.success?.length || 0;
            const failedCount = data.results?.failed?.length || 0;
            
            showToast(`Successfully placed ${successCount} orders, ${failedCount} failed`, 
                failedCount > 0 ? 'warning' : 'success');
            
            // Refresh table data
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                const event = new Event('input', { bubbles: true });
                searchInput.dispatchEvent(event);
            }
        })
        .catch(error => {
            // Reset button
            button.innerHTML = '<i class="fas fa-upload me-1"></i>Place Selected Orders on Kite';
            button.disabled = false;
            
            console.error('Error placing multiple orders:', error);
            showToast('Failed to place orders on Kite', 'error');
        });
}

/**
 * Reset an order's Kite status
 */
function resetOrder(orderId) {
    showConfirmationModal(
        'Reset Order Status',
        'Are you sure you want to reset this order\'s Kite status? This will not remove it from Kite but will allow you to place it again.',
        () => {
            fetch(`/custom-gtt/reset-kite-status/${orderId}`, {
                method: 'POST'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showToast(data.error, 'error');
                        return;
                    }
                    
                    showToast('Order status reset successfully', 'success');
                    
                    // Refresh table data
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput) {
                        const event = new Event('input', { bubbles: true });
                        searchInput.dispatchEvent(event);
                    }
                })
                .catch(error => {
                    console.error('Error resetting order status:', error);
                    showToast('Failed to reset order status', 'error');
                });
        }
    );
}

/**
 * Initialize sorting functionality
 */
function initializeSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.getAttribute('data-column');
            sortTable(column);
        });
    });
    console.log('✅ Sorting functionality initialized');
}

/**
 * Sort table by column
 */
function sortTable(column) {
    // Toggle sort direction if same column
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }
    
    // Update header styling
    updateSortHeaders();
    
    // Trigger search with current parameters and sort
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        const event = new Event('input', { bubbles: true });
        searchInput.dispatchEvent(event);
    } else {
        // If no search input, load data with sort parameters
        loadTableData();
    }
    
    console.log(`Sorted by ${column} (${currentSortDirection})`);
}

/**
 * Update sort header styling
 */
function updateSortHeaders() {
    // Reset all headers
    document.querySelectorAll('.sortable').forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Set current sorted header
    if (currentSortColumn) {
        const currentHeader = document.querySelector(`[data-column="${currentSortColumn}"]`);
        if (currentHeader) {
            currentHeader.classList.add(`sort-${currentSortDirection}`);
        }
    }
}

/**
 * Load table data with current filters and sorting
 */
function loadTableData() {
    const orderTypeFilter = document.getElementById('orderTypeFilter');
    const kiteStatusFilter = document.getElementById('kiteStatusFilter');
    const recordsPerPage = document.getElementById('recordsPerPage');
    const searchInput = document.getElementById('searchInput');
    
    const params = new URLSearchParams({
        page: 1,
        per_page: recordsPerPage ? recordsPerPage.value : 25
    });
    
    if (searchInput && searchInput.value) {
        params.append('search', searchInput.value);
    }
    
    if (orderTypeFilter && orderTypeFilter.value) {
        params.append('order_type', orderTypeFilter.value);
    }
    
    if (kiteStatusFilter && kiteStatusFilter.value) {
        params.append('kite_status', kiteStatusFilter.value);
    }
    
    // Add sorting parameters
    if (currentSortColumn) {
        params.append('sort_by', currentSortColumn);
        params.append('sort_order', currentSortDirection);
    }
    
    fetch(`/api/custom-gtt/orders?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            updateOrdersTable(data);
        })
        .catch(error => {
            console.error('Error loading table data:', error);
            showToast('Failed to load data', 'error');
        });
}

/**
 * Show confirmation modal
 */
function showConfirmationModal(title, message, confirmCallback) {
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    
    document.getElementById('confirmationTitle').textContent = title;
    document.getElementById('confirmationBody').textContent = message;
    
    const confirmButton = document.getElementById('confirmActionBtn');
    
    // Remove previous event listeners
    const newConfirmButton = confirmButton.cloneNode(true);
    confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
    
    // Add new event listener
    newConfirmButton.addEventListener('click', () => {
        modal.hide();
        confirmCallback();
    });
    
    modal.show();
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    const iconClass = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';
    
    toast.className = `toast ${bgClass} text-white`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <i class="${iconClass} me-2"></i>
            <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '5000';
    document.body.appendChild(container);
    return container;
}

/**
 * Validate that all modal elements exist and Bootstrap is properly loaded
 */
function validateModalElements() {
    console.log('Validating modal elements...');
    
    // Check if Bootstrap is properly loaded
    if (typeof bootstrap === 'undefined' || typeof bootstrap.Modal === 'undefined') {
        console.error('Bootstrap not loaded properly!');
        showToast('Error: Bootstrap library not loaded properly. Please refresh the page.', 'error');
        return false;
    }
    
    // Check modal elements
    const modalChecklist = [
        { id: 'orderModal', name: 'Order Modal' },
        { id: 'orderModalTitle', name: 'Modal Title' },
        { id: 'orderForm', name: 'Order Form' },
        { id: 'saveOrderBtn', name: 'Save Order Button' }
    ];
    
    let allFound = true;
    modalChecklist.forEach(item => {
        const element = document.getElementById(item.id);
        if (!element) {
            console.error(`${item.name} (${item.id}) not found!`);
            allFound = false;
        } else {
            console.log(`${item.name} (${item.id}) found OK`);
        }
    });
    
    return allFound;
}

// Validate modal elements on page load
document.addEventListener('DOMContentLoaded', () => {
    validateModalElements();
});

/**
 * Initialize missing DOM elements that are required by the JavaScript
 */
function initializeMissingElements() {
    const requiredElements = [
        { id: 'totalAmount', defaultValue: '0.00', parent: null },
        { id: 'totalAllAmount', defaultValue: '0.00', parent: null },
        { id: 'currentRecords', defaultValue: '0', parent: null },
        { id: 'totalRecords', defaultValue: '0', parent: null },
        { id: 'selectedCount', defaultValue: '0', parent: null }
    ];
    
    requiredElements.forEach(({ id, defaultValue, parent }) => {
        let element = document.getElementById(id);
        
        if (!element) {
            console.warn(`Creating missing element: ${id}`);
            element = document.createElement('span');
            element.id = id;
            element.textContent = defaultValue;
            element.style.display = 'none'; // Hide if no proper parent
            
            // Try to find a reasonable parent or append to body
            if (parent) {
                const parentEl = document.querySelector(parent);
                if (parentEl) {
                    parentEl.appendChild(element);
                } else {
                    document.body.appendChild(element);
                }
            } else {
                document.body.appendChild(element);
            }
        }
    });
}

/**
 * Safe text content setter that checks if element exists
 */
function safeSetTextContent(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    } else {
        console.warn(`Element ${elementId} not found when trying to set textContent to "${value}"`);
    }
}

// Initialize missing elements on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeMissingElements();
});

// Debug function for main page inspection
function performTableDebug() {
    const debugInfo = {
        timestamp: new Date().toLocaleTimeString(),
        page_url: window.location.href,
        table_exists: !!document.getElementById('customGttTable'),
        tbody_exists: !!document.getElementById('customGttTableBody'),
        table_visible: false,
        tbody_content_length: 0,
        tbody_children_count: 0,
        css_loaded: false,
        js_functions_available: {},
        dom_ready_state: document.readyState
    };
    
    // Check table visibility
    const table = document.getElementById('customGttTable');
    if (table) {
        const computedStyle = window.getComputedStyle(table);
        debugInfo.table_visible = (
            computedStyle.display !== 'none' && 
            computedStyle.visibility !== 'hidden' &&
            computedStyle.opacity !== '0'
        );
        debugInfo.table_styles = {
            display: computedStyle.display,
            visibility: computedStyle.visibility,
            opacity: computedStyle.opacity,
            height: computedStyle.height,
            width: computedStyle.width
        };
    }
    
    // Check tbody content
    const tbody = document.getElementById('customGttTableBody');
    if (tbody) {
        debugInfo.tbody_content_length = tbody.innerHTML.length;
        debugInfo.tbody_children_count = tbody.children.length;
        debugInfo.tbody_content_preview = tbody.innerHTML.substring(0, 200);
    }
    
    // Check CSS loading
    const testElement = document.createElement('div');
    testElement.className = 'table table-striped';
    document.body.appendChild(testElement);
    const testStyle = window.getComputedStyle(testElement);
    debugInfo.css_loaded = testStyle.width !== 'auto';
    document.body.removeChild(testElement);
    
    // Check JavaScript functions
    const functionsToCheck = ['updateOrdersTable', 'initializeSearch', 'safeSetTextContent', 'calculateAmount', 'formatCurrency'];
    functionsToCheck.forEach(funcName => {
        debugInfo.js_functions_available[funcName] = typeof window[funcName] === 'function';
    });
    
    // Display debug info
    const debugWindow = window.open('', 'debug', 'width=800,height=600');
    debugWindow.document.write(`
        <html>
            <head><title>Table Debug Info</title></head>
            <body style="font-family: monospace; padding: 20px;">
                <h2>🐛 Table Debug Information</h2>
                <pre style="background: #f5f5f5; padding: 15px; border: 1px solid #ddd;">
${JSON.stringify(debugInfo, null, 2)}
                </pre>
                <hr>
                <h3>Quick Fixes to Try:</h3>
                <button onclick="opener.testTableFix1(); window.focus();">Fix 1: Force Table Visibility</button><br><br>
                <button onclick="opener.testTableFix2(); window.focus();">Fix 2: Reload Table Data</button><br><br>
                <button onclick="opener.testTableFix3(); window.focus();">Fix 3: Add Test Row</button><br><br>
                <button onclick="window.close();">Close</button>
            </body>
        </html>
    `);
    
    console.log('🐛 Table Debug Info:', debugInfo);
    return debugInfo;
}

// Quick fix functions
function testTableFix1() {
    console.log('🔧 Applying Fix 1: Force table visibility');
    const table = document.getElementById('customGttTable');
    if (table) {
        table.style.display = 'table';
        table.style.visibility = 'visible';
        table.style.opacity = '1';
        table.style.height = 'auto';
        table.style.backgroundColor = 'white';
        table.style.border = '2px solid red';
        console.log('✅ Applied visibility fixes to table');
    }
}

function testTableFix2() {
    console.log('🔧 Applying Fix 2: Reload table data');
    fetch('/api/custom-gtt/orders')
        .then(response => response.json())
        .then(data => {
            console.log('📊 Reloaded data:', data);
            if (typeof updateOrdersTable === 'function') {
                updateOrdersTable(data);
                console.log('✅ Called updateOrdersTable with fresh data');
            } else {
                console.error('❌ updateOrdersTable function not available');
            }
        })
        .catch(error => {
            console.error('❌ Failed to reload data:', error);
        });
}

function testTableFix3() {
    console.log('🔧 Applying Fix 3: Add test row');
    const tbody = document.getElementById('customGttTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr style="background: yellow; border: 3px solid red; height: 40px;">
                <td style="border: 1px solid black; font-weight: bold;"><input type="checkbox"></td>
                <td style="border: 1px solid black; font-weight: bold; color: red;">DEBUG_TEST</td>
                <td style="border: 1px solid black; font-weight: bold;">DEBUG COMPANY</td>
                <td style="border: 1px solid black; font-weight: bold;">NSE</td>
                <td style="border: 1px solid black; font-weight: bold;">BUY</td>
                <td style="border: 1px solid black; font-weight: bold;">2500</td>
                <td style="border: 1px solid black; font-weight: bold;">2480</td>
                <td style="border: 1px solid black; font-weight: bold;">10</td>
                <td style="border: 1px solid black; font-weight: bold;">₹24,800</td>
                <td style="border: 1px solid black; font-weight: bold;">DEBUG ROW</td>
                <td style="border: 1px solid black; font-weight: bold;"><span class="badge bg-warning">DEBUG</span></td>
                <td style="border: 1px solid black; font-weight: bold;">
                    <button class="btn btn-sm btn-danger">DEBUG</button>
                </td>
            </tr>
        `;
        console.log('✅ Added debug test row');
    } else {
        console.error('❌ Table body not found');
    }
}

/**
 * Debug function to visualize table column alignment
 */
function toggleTableDebugBorders() {
    const table = document.getElementById('customGttTable');
    if (table) {
        table.classList.toggle('debug-borders');
        console.log('Table debug borders toggled');
        
        // Log column widths for debugging
        const headers = table.querySelectorAll('thead th');
        const firstRow = table.querySelector('tbody tr:first-child');
        
        console.log('=== COLUMN WIDTH DEBUG ===');
        headers.forEach((th, index) => {
            const headerWidth = th.getBoundingClientRect().width;
            let cellWidth = 'N/A';
            
            if (firstRow) {
                const td = firstRow.cells[index];
                if (td) {
                    cellWidth = td.getBoundingClientRect().width;
                }
            }
            
            console.log(`Column ${index + 1}: Header=${headerWidth}px, Cell=${cellWidth}px`);
        });
        console.log('========================');
    }
}

// Make the debug function globally available
window.toggleTableDebugBorders = toggleTableDebugBorders;

/**
 * Apply grid layout for better alignment
 */
function applyGridLayout() {
    const table = document.getElementById('customGttTable');
    if (table) {
        table.classList.add('use-grid');
        console.log('Applied grid layout to table');
    }
}

/**
 * Remove grid layout
 */
function removeGridLayout() {
    const table = document.getElementById('customGttTable');
    if (table) {
        table.classList.remove('use-grid');
        console.log('Removed grid layout from table');
    }
}

// Make functions globally available
window.applyGridLayout = applyGridLayout;
window.removeGridLayout = removeGridLayout;
