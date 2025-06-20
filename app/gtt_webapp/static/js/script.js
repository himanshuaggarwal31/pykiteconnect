// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Format numbers
function formatNumber(number) {
    return new Intl.NumberFormat('en-IN').format(number);
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Confirm delete
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Show loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'position-fixed top-50 start-50 translate-middle';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(spinner);
    return spinner;
}

// Hide loading spinner
function hideLoading(spinner) {
    if (spinner && spinner.parentNode) {
        spinner.parentNode.removeChild(spinner);
    }
}

// Handle form submission
function handleFormSubmit(formElement, successCallback, errorCallback) {
    formElement.addEventListener('submit', async (e) => {
        e.preventDefault();
        const spinner = showLoading();
        
        try {
            const formData = new FormData(formElement);
            const response = await fetch(formElement.action, {
                method: formElement.method,
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                successCallback(data);
            } else {
                errorCallback(data.error || 'Something went wrong');
            }
        } catch (error) {
            errorCallback(error.message);
        } finally {
            hideLoading(spinner);
        }
    });
}

// Update table row
function updateTableRow(tableId, rowIndex, data) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const row = table.rows[rowIndex];
    if (!row) return;
    
    Object.entries(data).forEach(([key, value]) => {
        const cell = row.querySelector(`[data-field="${key}"]`);
        if (cell) {
            cell.textContent = value;
        }
    });
}

// Format date
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed bottom-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">Success</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                Copied to clipboard!
            </div>
        `;
        
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    });
}

// Density control logic for DataTables
window.setTableDensity = function(density) {
    const table = $('#ordersTable');
    if (density === 'compact') {
        table.removeClass('table-normal').addClass('table-compact');
    } else {
        table.removeClass('table-compact').addClass('table-normal');
    }
    localStorage.setItem('tableDensity', density);
    window.updateDensityButtons(density);
}

window.updateDensityButtons = function(density) {
    $('#compactView').toggleClass('active', density === 'compact');
    $('#normalView').toggleClass('active', density === 'normal');
}

$(document).ready(function() {
    // Set initial density class before DataTables initializes
    let currentDensity = localStorage.getItem('tableDensity') || 'compact';
    window.setTableDensity(currentDensity);

    // Initialize DataTables
    if ($('#ordersTable').length) {
        const dt = $('#ordersTable').DataTable({
            order: [[0, 'asc']],
            pageLength: 25,
            autoWidth: false
        });
        // Re-apply density class on every table draw
        dt.on('draw', function() {
            let density = localStorage.getItem('tableDensity') || 'compact';
            window.setTableDensity(density);
        });
    }
    // Update button states
    window.updateDensityButtons(currentDensity);
});
