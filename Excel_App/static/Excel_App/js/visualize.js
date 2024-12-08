// Global variables
let hasUnsavedChanges = false;
let currentData = null;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
});

async function initializePage() {
    showLoading(true);
    try {
        await fetchData();
        showLoading(false);
    } catch (error) {
        showError('Error loading data: ' + error.message);
        showLoading(false);
    }
}

async function fetchData() {
    try {
        const response = await fetch(`/get_file_data/${window.fileIndex}/`, {
            headers: {
                'X-CSRFToken': window.csrfToken,
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch data');
        }

        currentData = data;
        createTable(data.data);
        updateColumnSelect(data.data);
        updateFileInfo(data.file_info);
        showSuccess('Data loaded successfully');
    } catch (error) {
        console.error('Error fetching data:', error);
        showError('Failed to load data');
        throw error;
    }
}

function createTable(data) {
    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');
    
    if (!data || !data.columns || !data.values) {
        showError('Invalid data format');
        return;
    }

    // Clear existing content
    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';

    // Create header
    data.columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        tableHeader.appendChild(th);
    });

    // Create body
    data.values.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell !== null ? cell : '';
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });

    // Update row count
    updateFilteredRowCount();
}

function updateFileInfo(fileInfo) {
    if (!fileInfo) return;

    const elements = {
        fileName: document.getElementById('fileName'),
        fileSize: document.getElementById('fileSize'),
        uploadTime: document.getElementById('uploadTime'),
        rowCount: document.getElementById('totalRows'),
        columnCount: document.getElementById('totalColumns')
    };

    // Update each element if it exists
    Object.entries(elements).forEach(([key, element]) => {
        if (element && fileInfo[key]) {
            element.textContent = fileInfo[key];
        }
    });
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.classList.toggle('hidden', !show);
    }
}

function showError(message) {
    const toast = document.getElementById('errorToast');
    const toastBody = toast.querySelector('.toast-body');
    toastBody.textContent = message;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function showSuccess(message) {
    const toast = document.getElementById('successToast');
    const toastBody = toast.querySelector('.toast-body');
    toastBody.textContent = message;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Search and filter functionality
function filterAndSearchTable() {
    const searchTerm = document.getElementById('tableSearch').value.toLowerCase();
    const filterColumn = document.getElementById('columnFilter').value;
    const filterVal = document.getElementById('filterValue').value.toLowerCase();
    const rows = document.getElementById('tableBody').getElementsByTagName('tr');
    const headers = document.getElementById('tableHeader').getElementsByTagName('th');
    
    const filterColumnIndex = filterColumn ? 
        Array.from(headers).findIndex(th => th.textContent === filterColumn) : -1;

    Array.from(rows).forEach(row => {
        const cells = row.getElementsByTagName('td');
        let showRow = true;

        // Apply column filter
        if (filterColumnIndex !== -1 && filterVal) {
            const cellValue = cells[filterColumnIndex].textContent.toLowerCase();
            showRow = cellValue.includes(filterVal);
        }

        // Apply search across all columns
        if (showRow && searchTerm) {
            showRow = Array.from(cells).some(cell => 
                cell.textContent.toLowerCase().includes(searchTerm)
            );
        }

        row.style.display = showRow ? '' : 'none';
    });

    updateFilteredRowCount();
}

function updateFilteredRowCount() {
    const totalRows = document.getElementById('tableBody').getElementsByTagName('tr').length;
    const visibleRows = Array.from(document.getElementById('tableBody').getElementsByTagName('tr'))
        .filter(row => row.style.display !== 'none').length;
    
    const rowCountElement = document.getElementById('rowCount');
    if (rowCountElement) {
        rowCountElement.textContent = visibleRows === totalRows ? 
            `Total rows: ${totalRows}` : 
            `Showing ${visibleRows} of ${totalRows} rows`;
    }
}

function updateColumnSelect(data) {
    const columnSelect = document.getElementById('columnSelect');
    const columnFilter = document.getElementById('columnFilter');
    
    if (!data || !data.columns) return;

    // Clear existing options
    columnSelect.innerHTML = '<option value="">Select column...</option>';
    columnFilter.innerHTML = '<option value="">Select column to filter...</option>';

    // Add options for each column
    data.columns.forEach(column => {
        // For analysis
        const option1 = document.createElement('option');
        option1.value = column;
        option1.textContent = column;
        columnSelect.appendChild(option1);

        // For filtering
        const option2 = document.createElement('option');
        option2.value = column;
        option2.textContent = column;
        columnFilter.appendChild(option2);
    });
}

// Event listeners
document.getElementById('tableSearch').addEventListener('input', filterAndSearchTable);
document.getElementById('filterValue').addEventListener('input', filterAndSearchTable);
document.getElementById('columnFilter').addEventListener('change', filterAndSearchTable);
document.getElementById('clearFilter').addEventListener('click', () => {
    document.getElementById('tableSearch').value = '';
    document.getElementById('columnFilter').value = '';
    document.getElementById('filterValue').value = '';
    filterAndSearchTable();
});

// Statistical calculations
document.getElementById('calculateBtn').addEventListener('click', () => {
    const column = document.getElementById('columnSelect').value;
    const type = document.getElementById('calculationType').value;
    
    if (!column || !type) {
        showError('Please select both a column and calculation type');
        return;
    }
    
    try {
        const result = calculateStatistics(currentData.data, column, type);
        displayCalculationResult(result, type);
        showSuccess('Calculation completed successfully!');
    } catch (error) {
        console.error('Calculation error:', error);
        showError('Error performing calculation');
    }
});

function calculateStatistics(data, column, type) {
    if (!data || !data.columns || !data.values) {
        throw new Error('Invalid data format');
    }

    const columnIndex = data.columns.indexOf(column);
    if (columnIndex === -1) {
        throw new Error('Column not found');
    }

    const values = data.values
        .map(row => row[columnIndex])
        .filter(val => val !== null && val !== '' && !isNaN(Number(val)))
        .map(Number);

    if (values.length === 0) {
        throw new Error('No numeric values found in selected column');
    }

    switch (type) {
        case 'sum':
            return values.reduce((a, b) => a + b, 0);
        case 'average':
            return values.reduce((a, b) => a + b, 0) / values.length;
        case 'min':
            return Math.min(...values);
        case 'max':
            return Math.max(...values);
        case 'count':
            return values.length;
        default:
            throw new Error('Invalid calculation type');
    }
}

function displayCalculationResult(result, type) {
    const resultElement = document.getElementById('calculationResult');
    let formattedResult = result;
    
    // Format number based on type
    if (type === 'average') {
        formattedResult = result.toFixed(2);
    } else if (type === 'sum') {
        formattedResult = result.toLocaleString(undefined, { 
            minimumFractionDigits: 0,
            maximumFractionDigits: 2 
        });
    }

    resultElement.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)}: ${formattedResult}`;
}

// Copy result functionality
document.getElementById('copyResult').addEventListener('click', async () => {
    const result = document.getElementById('calculationResult').textContent;
    if (result === 'No calculation performed yet') {
        showError('No result to copy');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(result);
        showSuccess('Result copied to clipboard!');
    } catch (err) {
        showError('Failed to copy result');
    }
});
