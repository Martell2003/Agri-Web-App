// app/static/js/script.js

// Wait for the DOM to load
document.addEventListener('DOMContentLoaded', function () {
    console.log('Script loaded!');

    // Add event listeners and other logic here
});


// Handle form submission
document.getElementById('price-form').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent the default form submission

    // Get form data
    const formData = new FormData(this);

    // Send data to the server using Fetch API
    fetch('/submit-price', {
        method: 'POST',
        body: formData,
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            alert('Price submitted successfully!');
            // Optionally, update the UI with the new data
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to submit price. Please try again.');
        });
});


// Fetch and display price data
function fetchAndDisplayPrices() {
    fetch('/api/prices')
        .then(response => response.json())
        .then(data => {
            const priceList = document.getElementById('price-list');
            priceList.innerHTML = ''; // Clear existing content

            // Loop through the data and create list items
            data.forEach(price => {
                const listItem = document.createElement('li');
                listItem.textContent = `${price.product}: $${price.price}`;
                priceList.appendChild(listItem);
            });
        })
        .catch(error => {
            console.error('Error fetching prices:', error);
        });
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', fetchAndDisplayPrices);


// Initialize a chart
function initializeChart() {
    const ctx = document.getElementById('price-chart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line', // Line chart
        data: {
            labels: [], // X-axis labels (e.g., dates)
            datasets: [{
                label: 'Price',
                data: [], // Y-axis data (e.g., prices)
                borderColor: 'rgba(75, 192, 192, 1)',
                fill: false,
            }],
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date',
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: 'Price',
                    },
                },
            },
        },
    });

    // Fetch data and update the chart
    fetch('/api/prices')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.timestamp);
            const prices = data.map(item => item.price);

            chart.data.labels = labels;
            chart.data.datasets[0].data = prices;
            chart.update();
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
        });
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', initializeChart);

// Filter prices by product
document.getElementById('product-filter').addEventListener('change', function (event) {
    const selectedProduct = event.target.value;

    fetch(`/api/prices?product=${selectedProduct}`)
        .then(response => response.json())
        .then(data => {
            const priceList = document.getElementById('price-list');
            priceList.innerHTML = ''; // Clear existing content

            // Loop through the filtered data and create list items
            data.forEach(price => {
                const listItem = document.createElement('li');
                listItem.textContent = `${price.product}: $${price.price}`;
                priceList.appendChild(listItem);
            });
        })
        .catch(error => {
            console.error('Error fetching filtered prices:', error);
        });
});


function displayError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';

    // Hide the error message after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}


function updatePlotlyChart() {
    fetch('/api/prices')
        .then(response => response.json())
        .then(data => {
            const chartData = [{
                x: data.map(item => item.timestamp),
                y: data.map(item => item.price),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Price Trends',
            }];

            const layout = {
                title: 'Agricultural Price Trends',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Price' },
            };

            Plotly.react('plotly-chart', chartData, layout);
        })
        .catch(error => {
            console.error('Error updating Plotly chart:', error);
            displayError('Failed to update chart. Please try again.');
        });
}

// Call the function to update the chart
document.addEventListener('DOMContentLoaded', updatePlotlyChart);


function updateMatplotlibChart() {
    fetch('/api/prices')
        .then(response => response.json())
        .then(data => {
            const chartData = {
                labels: data.map(item => item.timestamp),
                prices: data.map(item => item.price),
            };

            // Send data to the server to generate a new chart
            fetch('/generate-chart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(chartData),
            })
                .then(response => response.json())
                .then(data => {
                    const chartImage = document.getElementById('matplotlib-chart');
                    chartImage.innerHTML = `<img src="data:image/png;base64,${data.chart}" alt="Matplotlib Chart">`;
                })
                .catch(error => {
                    console.error('Error updating Matplotlib chart:', error);
                    displayError('Failed to update chart. Please try again.');
                });
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
            displayError('Failed to fetch data. Please try again.');
        });
}

// Call the function to update the chart
document.addEventListener('DOMContentLoaded', updateMatplotlibChart);

//update chart based on selected product
document.getElementById('product-filter').addEventListener('change', function (event) {
    const selectedProduct = event.target.value;

    fetch(`/api/prices?product=${selectedProduct}`)
        .then(response => response.json())
        .then(data => {
            // Update the Plotly chart
            const chartData = [{
                x: data.map(item => item.timestamp),
                y: data.map(item => item.price),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Price Trends',
            }];

            const layout = {
                title: 'Agricultural Price Trends',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Price' },
            };

            Plotly.react('plotly-chart', chartData, layout);
        })
        .catch(error => {
            console.error('Error filtering data:', error);
            displayError('Failed to filter data. Please try again.');
        });
});

//Frontend Javascript Fetches data from backend and updates the charts dynamically
function updatePlotlyChart() {
    fetch('/api/prices')
        .then(response => response.json())
        .then(data => {
            const chartData = [{
                x: data.map(item => item.timestamp),
                y: data.map(item => item.price),
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Price Trends',
            }];

            const layout = {
                title: 'Agricultural Price Trends',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Price' },
            };

            Plotly.react('plotly-chart', chartData, layout);
        })
        .catch(error => {
            console.error('Error updating Plotly chart:', error);
            displayError('Failed to update chart. Please try again.');
        });
}