// Global variables for table controls
let currentPage = 1;
let currentPerPage = 25;
let searchTimeout;
let currentSearch = '';

// Initialize table controls
function initializeTableControls(options = {}) {
    const {
        searchUrl = window.location.pathname + '/fetch',
        updateTableCallback,
        additionalParams = {}
    } = options;

    // Initialize search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentSearch = this.value;
                currentPage = 1; // Reset to first page on new search
                fetchTableData();
            }, 300);
        });
    }

    // Initialize records per page
    const perPageSelect = document.getElementById('recordsPerPage');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            currentPerPage = parseInt(this.value);
            currentPage = 1; // Reset to first page when changing per_page
            fetchTableData();
        });
    }

    // Set initial values from URL params
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('search')) {
        currentSearch = urlParams.get('search');
        if (searchInput) searchInput.value = currentSearch;
    }
    if (urlParams.has('per_page')) {
        currentPerPage = parseInt(urlParams.get('per_page'));
        if (perPageSelect) perPageSelect.value = currentPerPage;
    }
    if (urlParams.has('page')) {
        currentPage = parseInt(urlParams.get('page'));
    }

    // Function to fetch data
    function fetchTableData() {
        const params = new URLSearchParams({
            search: currentSearch,
            page: currentPage,
            per_page: currentPerPage,
            ...additionalParams
        });

        fetch(`${searchUrl}?${params}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    return;
                }

                // Update the table using the provided callback
                if (updateTableCallback) {
                    updateTableCallback(data);
                }

                // Update records info
                const currentRecords = document.getElementById('currentRecords');
                const totalRecords = document.getElementById('totalRecords');
                if (currentRecords) currentRecords.textContent = data.records.length;
                if (totalRecords) totalRecords.textContent = data.total_count;

                // Update URL with current filters
                const newUrl = `${window.location.pathname}?${params}`;
                history.pushState({}, '', newUrl);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                showError('Failed to fetch data');
            });
    }

    // Initial fetch
    fetchTableData();

    // Return the fetch function for external use
    return fetchTableData;
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.content-wrapper').prepend(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}
