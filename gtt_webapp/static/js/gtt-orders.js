document.addEventListener('DOMContentLoaded', function() {
    // Initial data load
    loadGTTOrders();
});

function loadGTTOrders() {
    fetch('/custom-gtt/fetch')
        .then(response => response.json())
        .then(data => updateOrdersTable(data.records || []))
        .catch(error => showError('Failed to load GTT orders: ' + error.message));
}

function updateOrdersTable(orders) {
    const tbody = document.getElementById('customGttTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    orders.forEach(order => {
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
            <td class="editable-cell" data-field="tags">${order.tags || ''}</td>
            <td>
                <span class="badge bg-${order.placed_on_kite ? 'success' : 'secondary'}">
                    ${order.placed_on_kite ? 'On Kite' : 'Local'}
                </span>
            </td>
            <td class="action-buttons">
                ${!order.placed_on_kite ? `<button class="btn btn-sm btn-success action-btn" onclick="placeOrderOnKite(${order.id})" title="Place on Kite"><i class="fas fa-upload"></i> Place</button>` : `<button class="btn btn-sm btn-warning action-btn" onclick="resetKiteStatus(${order.id})" title="Reset Kite Status"><i class="fas fa-undo"></i> Reset</button>`}
                <button class="btn btn-sm btn-danger action-btn ms-2" onclick="deleteOrder(${order.id})" title="Delete"><i class="fas fa-trash"></i> Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
