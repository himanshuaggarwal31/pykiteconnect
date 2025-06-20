// Shared search functionality
function initializeSearch(options = {}) {
    const {
        searchInputId = 'searchInput',
        tableId = 'dataTable',
        fetchUrl,
        updateCallback,
        searchFields = [],
        additionalParams = {}
    } = options;

    let searchTimeout;
    const searchInput = document.getElementById(searchInputId);
    if (!searchInput) {
        console.error('Search input element not found');
        return;
    }

    // Initialize search input events
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchData();
        }, 300);
    });

    // Function to show error messages
    function showError(message, isSystemError = false) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.setAttribute('role', 'alert');
        
        // Add icon and format message
        const errorContent = isSystemError ? 
            `<i class="fas fa-exclamation-triangle me-2"></i>System Error: ${message}` :
            `<i class="fas fa-exclamation-circle me-2"></i>${message}`;
        
        errorDiv.innerHTML = `
            ${errorContent}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Remove any existing error messages
        const existingErrors = document.querySelectorAll('.alert-danger');
        existingErrors.forEach(err => err.remove());

        // Insert the error message at the top of the table
        const table = document.getElementById(tableId);
        if (table && table.parentNode) {
            table.parentNode.insertBefore(errorDiv, table);
        } else {
            document.querySelector('.content-wrapper').insertBefore(errorDiv, document.querySelector('.content-wrapper').firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Function to fetch data with search
    function fetchData() {
        const searchValue = searchInput.value.trim();
        const params = new URLSearchParams();

        // Add search parameter
        if (searchValue) {
            params.append('search', searchValue);
        }

        // Add additional parameters
        Object.entries(additionalParams).forEach(([key, value]) => {
            if (typeof value === 'function') {
                const paramValue = value();
                if (paramValue) params.append(key, paramValue);
            } else if (value) {
                params.append(key, value);
            }
        });

        // Add records per page if available
        const recordsPerPage = document.getElementById('recordsPerPage');
        if (recordsPerPage) {
            params.append('per_page', recordsPerPage.value);
        }

        // Show loading state
        const table = document.getElementById(tableId);
        if (table) {
            table.classList.add('loading');
        }

        // Fetch data from server
        fetch(`${fetchUrl}?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    return;
                }

                // Update table via callback
                if (updateCallback) {
                    updateCallback(data);
                }

                // Update records info if elements exist
                const currentRecords = document.getElementById('currentRecords');
                const totalRecords = document.getElementById('totalRecords');
                if (currentRecords && totalRecords) {
                    currentRecords.textContent = data.records.length;
                    totalRecords.textContent = data.total_count;
                }

                // Update URL to make it bookmarkable
                const newUrl = `${window.location.pathname}?${params.toString()}`;
                history.pushState({}, '', newUrl);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                const errorMessage = error.message === 'Failed to fetch' ?
                    'Network error: Please check your internet connection' :
                    `Error: ${error.message}`;
                showError(errorMessage, true);
            })
            .finally(() => {
                // Remove loading state
                if (table) {
                    table.classList.remove('loading');
                }
            });
    }

    // Initialize records per page if available
    const recordsPerPage = document.getElementById('recordsPerPage');
    if (recordsPerPage) {
        recordsPerPage.addEventListener('change', fetchData);
    }

    // Set initial values from URL params
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('search')) {
        searchInput.value = urlParams.get('search');
    }
    if (urlParams.has('per_page') && recordsPerPage) {
        recordsPerPage.value = urlParams.get('per_page');
    }

    // Initial fetch
    fetchData();

    // Return fetch function for external use
    return fetchData;
}

<link rel="stylesheet" href="{{ url_for('static', filename='css/loading.css') }}">
