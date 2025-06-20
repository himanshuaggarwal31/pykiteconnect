document.addEventListener('DOMContentLoaded', function() {
    // Initialize search and table controls for Custom GTT Orders
    const fetchTableData = initializeSearch({
        searchInputId: 'orderSearch',
        tableId: 'customGttTable',
        fetchUrl: '/custom-gtt/fetch',
        updateCallback: updateOrdersTable,
        additionalParams: {
            order_type: () => document.getElementById('orderTypeFilter')?.value || '',
            kite_status: () => document.getElementById('kiteStatusFilter')?.value || ''
        }
    });

    // Add filter change handlers
    ['orderTypeFilter', 'kiteStatusFilter', 'recordsPerPage'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', fetchTableData);
        }
    });

    // Initialize select all checkbox
    const selectAllCheckbox = document.getElementById('selectAllOrders');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.order-select:not(:disabled)');
            checkboxes.forEach(checkbox => checkbox.checked = this.checked);
        });
    }
});

function updateOrdersTable(data) {
    const tbody = document.querySelector('#customGttTable tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    data.records.forEach(order => {
        const tr = document.createElement('tr');
        tr.dataset.id = order.id;
        tr.innerHTML = `
            <td><input type="checkbox" class="order-select" value="${order.id}"></td>
            <td class="editable-cell" data-field="symbol">${order.symbol}</td>
            <td class="editable-cell" data-field="company_name">${order.company_name || ''}</td>
            <td class="editable-cell" data-field="nifty_rank">${order.nifty_rank || ''}</td>
            <td class="editable-cell" data-field="order_type">${order.order_type}</td>
            <td class="editable-cell" data-field="trigger_price">${order.trigger_price}</td>
            <td class="editable-cell" data-field="last_price">${order.last_price || ''}</td>
            <td class="editable-cell" data-field="quantity">${order.quantity}</td>
            <td class="editable-cell" data-field="target_price">${order.target_price || ''}</td>
            <td class="editable-cell" data-field="stop_loss">${order.stop_loss || ''}</td>
            <td class="editable-cell" data-field="notes">${order.notes || ''}</td>
            <td class="editable-cell" data-field="tags">${order.tags || ''}</td>
            <td>${order.placed_on_kite ? '<span class="badge bg-success">On Kite</span>' : '<span class="badge bg-secondary">Local Only</span>'}</td>
            <td class="action-buttons">
                ${!order.placed_on_kite ? `<button class="btn btn-sm btn-success action-btn" onclick="placeOrderOnKite(${order.id})" title="Place on Kite"><i class="fas fa-upload"></i> Place</button>` : `<button class="btn btn-sm btn-warning action-btn" onclick="resetKiteStatus(${order.id})" title="Reset Kite Status"><i class="fas fa-undo"></i> Reset</button>`}
                <button class="btn btn-sm btn-danger action-btn ms-2" onclick="deleteOrder(${order.id})" title="Delete"><i class="fas fa-trash"></i> Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    // Update records info
    const currentRecords = document.getElementById('currentRecords');
    const totalRecords = document.getElementById('totalRecords');
    if (currentRecords && totalRecords) {
        currentRecords.textContent = data.records.length;
        totalRecords.textContent = data.total_count;
    }
}
