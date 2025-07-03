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
        console.log('[search.js] Fetching data...');
        const searchValue = searchInput.value.trim();
        const params = new URLSearchParams();

        // Add search parameter
        if (searchValue) {
            params.append('search', searchValue);
            console.log('[search.js] Added search param:', searchValue);
        }

        // Add additional parameters
        if (additionalParams && typeof additionalParams === 'object') {
            Object.entries(additionalParams).forEach(([key, value]) => {
                if (typeof value === 'function') {
                    const paramValue = value();
                    if (paramValue) {
                        params.append(key, paramValue);
                        console.log(`[search.js] Added param from function: ${key}=${paramValue}`);
                    }
                } else if (value) {
                    params.append(key, value);
                    console.log(`[search.js] Added param directly: ${key}=${value}`);
                }
            });
        }

        // Add records per page if available
        const recordsPerPage = document.getElementById('recordsPerPage');
        if (recordsPerPage) {
            params.append('per_page', recordsPerPage.value);
            console.log(`[search.js] Added per_page param: ${recordsPerPage.value}`);
        }

        // Add page parameter if needed
        const currentPage = document.getElementById('currentPage');
        if (currentPage) {
            const pageNum = currentPage.textContent || "1";
            params.append('page', pageNum);
            console.log(`[search.js] Added page param: ${pageNum}`);
        }

        // Show loading state
        const table = document.getElementById(tableId);
        if (table) {
            table.classList.add('loading');
            console.log('[search.js] Added loading class to table');
        } else {
            console.error('[search.js] Table element not found:', tableId);
        }

        const apiUrl = `${fetchUrl}?${params.toString()}`;
        console.log('[search.js] Fetching data from:', apiUrl);

        // Fetch data from server
        fetch(apiUrl)
            .then(response => {
                console.log('[search.js] Fetch response status:', response.status);
                console.log('[search.js] Fetch response headers:', response.headers);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('[search.js] Received data:', data);
                console.log('[search.js] Data type:', typeof data);
                console.log('[search.js] Data keys:', data ? Object.keys(data) : 'null/undefined');
                
                if (data.error) {
                    showError(data.error);
                    return;
                }

                // Update table via callback
                if (updateCallback) {
                    console.log('[search.js] Calling updateCallback with data');
                    updateCallback(data);
                    console.log('[search.js] updateCallback completed');
                } else {
                    console.error('[search.js] No updateCallback provided!');
                }

                // Update records info if elements exist
                const currentRecords = document.getElementById('currentRecords');
                const totalRecords = document.getElementById('totalRecords');
                if (currentRecords && totalRecords) {
                    currentRecords.textContent = data.records.length;
                    totalRecords.textContent = data.total_count;
                    console.log('[search.js] Updated record counts');
                } else {
                    console.warn('[search.js] Record count elements not found');
                }

                // Update URL to make it bookmarkable
                const newUrl = `${window.location.pathname}?${params.toString()}`;
                history.pushState({}, '', newUrl);
                console.log('[search.js] Updated URL:', newUrl);
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
