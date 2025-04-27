// trends.js - placed in app/static/js/
function renderPlotlyChart(chartId, graphJSON) {
    const chartContainer = document.getElementById(chartId);
    if (!chartContainer) {
        console.error(`Chart container with id "${chartId}" not found.`);
        return;
    }

    console.log('graphJSON:', graphJSON);
    if (graphJSON && graphJSON.data) {
        try {
            Plotly.newPlot(chartId, graphJSON.data, graphJSON.layout || {});
        } catch (error) {
            console.error('Error plotting graphJSON:', error);
            chartContainer.innerHTML = '<div class="alert alert-danger">Error: Could not render chart. Invalid data.</div>';
        }
    } else {
        chartContainer.innerHTML = '<div class="alert alert-danger">Error: No data was provided to render the chart.</div>';
    }
}

function initializeTableSort(tableId) {
    console.log(`Initializing sort for table: ${tableId}`);
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`Table with id "${tableId}" not found.`);
        return;
    }
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Table with id "${tableId}" has no tbody.`);
        return;
    }
    const sortableHeaders = table.querySelectorAll('.sortable');
    if (sortableHeaders.length === 0) {
        console.error(`Table with id "${tableId}" has no sortable headers.`);
        return;
    }

    let currentSortColumn = null;
    let sortDirection = 'asc';

    function sortTable(column, direction) {
        console.log(`Sorting table by ${column}, direction: ${direction}`);
        const rows = Array.from(tbody.rows);

        rows.sort((a, b) => {
            let aValue = a.dataset[column];
            let bValue = b.dataset[column];

            let comparison = 0;
            if (column === 'price') {
                aValue = aValue === 'N/A' ? -Infinity : parseFloat(aValue);
                bValue = bValue === 'N/A' ? -Infinity : parseFloat(bValue);
                comparison = aValue - bValue;
            } else if (column === 'time') {
                aValue = aValue === '' ? new Date(-8640000000000000) : new Date(aValue);
                bValue = bValue === '' ? new Date(-8640000000000000) : new Date(bValue);
                comparison = aValue - bValue;
            } else {
                aValue = aValue === 'N/A' ? '' : aValue;
                bValue = bValue === 'N/A' ? '' : bValue;
                comparison = aValue.localeCompare(bValue, undefined, {
                    sensitivity: 'base'
                });
            }
            return direction === 'asc' ? comparison : comparison * -1;
        });
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
    }

    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');
            if (currentSortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortColumn = column;
                sortDirection = 'asc';
            }
            sortTable(column, sortDirection);
            sortableHeaders.forEach(h => {
                const icon = h.querySelector('.sort-icon');
                if (h.getAttribute('data-sort') === column) {
                    h.classList.add(sortDirection);
                    icon.style.opacity = '1';
                    icon.style.transform = sortDirection === 'asc' ? 'rotate(0deg)' : 'rotate(180deg)';
                } else {
                    h.classList.remove('asc', 'desc');
                    icon.style.opacity = '0.6';
                    icon.style.transform = 'rotate(0deg)';
                }
            });
        });
    });
}

function initializeTableSearch(tableId, searchInputId) {
    console.log(`Initializing search for table: ${tableId}`);
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`Table with id "${tableId}" not found.`);
        return;
    }
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Table with id "${tableId}" has no tbody.`);
        return;
    }
    const searchInput = document.getElementById(searchInputId);
    if (!searchInput) {
        console.error(`Input with id "${searchInputId}" not found.`);
        return;
    }

    searchInput.addEventListener('input', () => {
        const filter = searchInput.value.toLowerCase();
        Array.from(tbody.rows).forEach(row => {
            const product = row.dataset.product.toLowerCase();
            const region = row.dataset.region.toLowerCase();
            const market = row.dataset.market.toLowerCase();
            const rowText = product + ' ' + region + ' ' + market + ' ' + row.textContent.toLowerCase();
            row.style.display = rowText.includes(filter) ? '' : 'none';
        });
    });
}