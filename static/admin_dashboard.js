// admin_dashboard.js - rewritten for new admin dashboard UI

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching (Bootstrap handles, but we can add logic if needed)
    // Load initial data for Home tab
    loadParkingLots();
    // Load initial summary charts
    renderSummaryCharts();
    // Users tab
    document.getElementById('users-tab').addEventListener('click', loadUsers);
    // Search tab
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
    // Add Enter key support for search
    document.getElementById('searchString').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    // Summary tab
    document.getElementById('summary-tab').addEventListener('click', function() {
        renderSummaryCharts();
    });
    // Add Lot button
    document.getElementById('addLotBtn').addEventListener('click', function() {
        const modal = new bootstrap.Modal(document.getElementById('newLotModal'));
        document.getElementById('newLotForm').reset();
        modal.show();
    });
    // New Lot form submit
    document.getElementById('newLotForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addParkingLot();
    });
    // Edit Lot form submit
    document.getElementById('editLotForm').addEventListener('submit', function(e) {
        e.preventDefault();
        updateParkingLot();
    });
    // Logout
    document.getElementById('logout-tab').addEventListener('click', function() {
        localStorage.clear();
        window.location.href = '/';
    });
    // Edit Profile button
    document.getElementById('editProfileBtn').addEventListener('click', function() {
        // Optionally, fetch current admin info here
        const modal = new bootstrap.Modal(document.getElementById('editProfileModal'));
        modal.show();
    });
    // Edit Profile form submit
    document.getElementById('editProfileForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const email = document.getElementById('adminEmail').value;
        const password = document.getElementById('adminPassword').value;
        fetch('/api/admin/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        .then(res => res.json())
        .then(data => {
            showToast(data.message || 'Profile updated!');
            bootstrap.Modal.getInstance(document.getElementById('editProfileModal')).hide();
        });
    });
});

// --- Parking Lots ---
function loadParkingLots() {
    fetch('/api/admin/lots')
        .then(res => res.json())
        .then(data => {
            const lotsContainer = document.getElementById('lotsContainer');
            lotsContainer.innerHTML = '';
            data.lots.forEach(lot => {
                const col = document.createElement('div');
                col.className = 'col-md-6 col-lg-4 mb-4';
                col.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="parking-lot-title" onclick="showLotDetailsModal(${lot.id})">${lot.location_name}</div>
                            <div>
                                <a href="#" class="text-primary me-2" onclick="showEditLotModal(${lot.id})">Edit</a>|
                                <a href="#" class="text-danger ms-2" onclick="deleteLot(${lot.id})">Delete</a>
                            </div>
                        </div>
                        <div class="mb-2 text-success">(Occupied : ${lot.occupied}/${lot.max_spots})</div>
                        <div class="occupancy-grid">
                            ${lot.spots.map(spot => `
                                <div class="spot-box spot-${spot.status}" title="Spot ${spot.id}" onclick="showSpotModal(${spot.id}, '${spot.status}')">
                                    ${spot.status === 'occupied' ? 'O' : 'A'}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>`;
                lotsContainer.appendChild(col);
            });
        });
}

function addParkingLot() {
    const maxSpots = parseInt(document.getElementById('newLotSpots').value);
    
    // Validate max spots limit
    if (maxSpots < 1 || maxSpots > 10) {
        showToast('Maximum spots must be between 1 and 10', 'error');
        return;
    }
    
    const data = {
        location_name: document.getElementById('newLotName').value,
        address: document.getElementById('newLotAddress').value,
        pin_code: document.getElementById('newLotPincode').value,
        price: document.getElementById('newLotPrice').value,
        max_spots: maxSpots
    };
    fetch('/api/admin/lots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(() => {
        loadParkingLots();
        renderSummaryCharts();
        bootstrap.Modal.getInstance(document.getElementById('newLotModal')).hide();
    });
}

function showEditLotModal(lotId) {
    fetch(`/api/admin/lots`)
        .then(res => res.json())
        .then(data => {
            const lot = data.lots.find(l => l.id === lotId);
            document.getElementById('editLotName').value = lot.location_name;
            document.getElementById('editLotAddress').value = lot.address;
            document.getElementById('editLotPincode').value = lot.pin_code;
            document.getElementById('editLotPrice').value = lot.price;
            document.getElementById('editLotSpots').value = lot.max_spots;
            document.getElementById('editLotForm').setAttribute('data-lot-id', lotId);
            const modal = new bootstrap.Modal(document.getElementById('editLotModal'));
            modal.show();
        });
}

function updateParkingLot() {
    const lotId = document.getElementById('editLotForm').getAttribute('data-lot-id');
    const newMaxSpots = parseInt(document.getElementById('editLotSpots').value);
    
    // Validate max spots limit
    if (newMaxSpots < 1 || newMaxSpots > 10) {
        showToast('Maximum spots must be between 1 and 10', 'error');
        return;
    }
    
    fetch(`/api/admin/lots`)
        .then(res => res.json())
        .then(data => {
            const lot = data.lots.find(l => l.id == lotId);
            const oldMaxSpots = lot.max_spots;
            // Update lot info
            const updateData = {
                location_name: document.getElementById('editLotName').value,
                address: document.getElementById('editLotAddress').value,
                pin_code: document.getElementById('editLotPincode').value,
                price: document.getElementById('editLotPrice').value,
                max_spots: newMaxSpots
            };
            fetch(`/api/admin/lots/${lotId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            })
            .then(() => {
                // Add or remove spots as needed
                if (newMaxSpots > oldMaxSpots) {
                    // Add spots
                    const addCount = newMaxSpots - oldMaxSpots;
                    const addSpotPromises = [];
                    for (let i = 0; i < addCount; i++) {
                        addSpotPromises.push(
                            fetch(`/api/admin/lots/${lotId}/spots`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ status: 'vacant' })
                            })
                        );
                    }
                    Promise.all(addSpotPromises).then(() => {
                        loadParkingLots();
                        renderSummaryCharts();
                        bootstrap.Modal.getInstance(document.getElementById('editLotModal')).hide();
                    });
                } else if (newMaxSpots < oldMaxSpots) {
                    // Remove vacant spots
                    fetch(`/api/admin/lots/${lotId}/spots`)
                        .then(res => res.json())
                        .then(data => {
                            const vacantSpots = data.spots.filter(s => s.status === 'vacant');
                            const removeCount = oldMaxSpots - newMaxSpots;
                            if (vacantSpots.length < removeCount) {
                                alert('Not enough vacant spots to remove!');
                                loadParkingLots();
                                renderSummaryCharts();
                                bootstrap.Modal.getInstance(document.getElementById('editLotModal')).hide();
                                return;
                            }
                            const removePromises = vacantSpots.slice(0, removeCount).map(spot =>
                                fetch(`/api/admin/spots/${spot.id}`, { method: 'DELETE' })
                            );
                            Promise.all(removePromises).then(() => {
                                loadParkingLots();
                                renderSummaryCharts();
                                bootstrap.Modal.getInstance(document.getElementById('editLotModal')).hide();
                            });
                        });
                } else {
                    loadParkingLots();
                    renderSummaryCharts();
                    bootstrap.Modal.getInstance(document.getElementById('editLotModal')).hide();
                }
            });
        });
}

function deleteLot(lotId) {
    // First fetch the lot details to check if any slot is occupied
    fetch('/api/admin/lots')
        .then(res => res.json())
        .then(data => {
            const lot = data.lots.find(l => l.id === lotId);
            if (lot && lot.occupied > 0) {
                alert('In this lot slot is occupied you can not delete this lot');
                return;
            }
            if (confirm('Are you sure you want to delete this parking lot?')) {
                fetch(`/api/admin/lots/${lotId}`, { method: 'DELETE' })
                    .then(() => {
                        loadParkingLots();
                        renderSummaryCharts();
                    });
            }
        });
}

function editLot(lotId) {
    const newMaxSpots = prompt("Enter new max spots:");
    if (!newMaxSpots) return;

    fetch(`/api/admin/lots/${lotId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_spots: parseInt(newMaxSpots) })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Error updating lot");
        loadParkingLots();
        // Hide the edit modal if it's open
        if (document.getElementById('editLotModal')) {
            bootstrap.Modal.getInstance(document.getElementById('editLotModal')).hide();
        }
    });
}

// --- Parking Spots ---
window.showSpotModal = function(spotId, status) {
    fetch(`/api/admin/spots/${spotId}`)
        .then(res => res.json())
        .then(spot => {
            if (spot.status === 'occupied') {
                document.getElementById('viewSpotId').value = spot.id;
                document.getElementById('viewSpotStatus').value = 'O';
                const occupiedFields = document.getElementById('occupiedFields');
                occupiedFields.style.display = '';
                document.getElementById('viewSpotCustomerId').value = spot.user_id || '';
                document.getElementById('viewSpotVehicleNumber').value = spot.vehicle_number || '';
                document.getElementById('viewSpotDateTime').value = spot.time_in || '';
                document.getElementById('viewSpotCost').value = '';
                // Optionally show user name/email
                // document.getElementById('viewSpotUserName').value = spot.user_name || '';
                // document.getElementById('viewSpotUserEmail').value = spot.user_email || '';
                const modal = new bootstrap.Modal(document.getElementById('viewSpotModal'));
                modal.show();
            } else {
                showToast('This spot is available.');
            }
        });
};

function showOccupiedSpotModal(spotId) {
    fetch(`/api/admin/spots/${spotId}/details`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('occupiedSpotId').value = data.id;
            document.getElementById('occupiedCustomerId').value = data.user_id;
            document.getElementById('occupiedVehicleNumber').value = data.vehicle_number;
            document.getElementById('occupiedDateTime').value = data.time_in;
            document.getElementById('occupiedCost').value = data.estimated_cost;
            const modal = new bootstrap.Modal(document.getElementById('occupiedSpotModal'));
            modal.show();
        });
}

function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast' + Date.now();
    const toast = document.createElement('div');
    const bgClass = type === 'error' ? 'text-bg-danger' : 'text-bg-success';
    toast.className = `toast align-items-center ${bgClass} border-0 show`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// --- Users ---
function loadUsers() {
    fetch('/api/admin/users')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = '';
            data.users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.id}</td>
                    <td>${user.email}</td>
                    <td>${user.full_name}</td>
                    <td>${user.address}</td>
                    <td>${user.pin_code}</td>
                `;
                tbody.appendChild(tr);
            });
        });
}

// --- Search ---
function handleSearch() {
    const by = document.getElementById('searchBy').value;
    const str = document.getElementById('searchString').value.trim();
    const results = document.getElementById('searchResults');
    
    // Validate input
    if (!str) {
        results.innerHTML = '<div class="alert alert-warning">Please enter a search term.</div>';
        return;
    }
    
    // Show loading state
    results.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Searching...</span></div></div>';
    
    fetch(`/api/admin/search?by=${by}&q=${encodeURIComponent(str)}`)
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            results.innerHTML = '';
            if (data.results && data.results.length > 0) {
                data.results.forEach(item => {
                    results.innerHTML += item; // Remove the extra div wrapper since HTML is already formatted
                });
            } else {
                results.innerHTML = '<div class="alert alert-info">No results found for your search.</div>';
            }
        })
        .catch(error => {
            console.error('Search error:', error);
            results.innerHTML = '<div class="alert alert-danger">An error occurred while searching. Please try again.</div>';
        });
}

// Update search placeholder based on selected search type
function updateSearchPlaceholder() {
    const searchBy = document.getElementById('searchBy').value;
    const searchInput = document.getElementById('searchString');
    
    if (searchBy === 'user') {
        searchInput.placeholder = 'Enter user ID (e.g., 1, 2, 3...)';
    } else if (searchBy === 'location') {
        searchInput.placeholder = 'Enter location, address, or pin code (e.g., Velachery, Chennai, 600042)';
    }
    
    // Clear previous search results when changing search type
    document.getElementById('searchResults').innerHTML = '';
}

// Chart instances to track for updates
let revenueChart = null;
let occupancyChart = null;
let utilizationChart = null;
let activityChart = null;

// --- Summary Charts ---
function renderSummaryCharts() {
    if (window.Chart) {
        fetch('/api/admin/summary?ts=' + Date.now())
            .then(res => res.json())
            .then(data => {
                // Update statistics cards
                updateStatisticsCards(data);
                
                // Update all charts
                updateRevenueChart(data);
                updateOccupancyChart(data);
                updateUtilizationChart(data);
                updateActivityChart(data);
            })
            .catch(error => {
                console.error('Error loading summary data:', error);
                showEmptyCharts();
            });
    } else {
        showEmptyCharts();
    }
}

function updateStatisticsCards(data) {
    // Calculate totals
    const totalLots = data.revenue ? data.revenue.length : 0;
    const totalRevenue = data.revenue ? data.revenue.reduce((sum, lot) => sum + lot.revenue, 0) : 0;
    let totalOccupied = 0, totalVacant = 0;
    
    if (data.occupancy) {
        data.occupancy.forEach(lot => {
            totalOccupied += lot.occupied;
            totalVacant += lot.available;
        });
    }
    
    // Update DOM
    document.getElementById('totalLots').textContent = totalLots;
    document.getElementById('totalRevenue').textContent = `₹${totalRevenue.toLocaleString()}`;
    document.getElementById('totalOccupied').textContent = totalOccupied;
    document.getElementById('totalVacant').textContent = totalVacant;
}

function updateRevenueChart(data) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    
    if (revenueChart) {
        revenueChart.destroy();
    }
    
    if (!data.revenue || data.revenue.length === 0) {
        revenueChart = createEmptyChart(ctx, 'No revenue data available');
        return;
    }
    
    const lot_names = data.revenue.map(lot => lot.location_name);
    const revenues = data.revenue.map(lot => lot.revenue);
    const colors = generateColors(lot_names.length);
    
    revenueChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: lot_names,
            datasets: [{
                data: revenues,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ₹${context.parsed.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function updateOccupancyChart(data) {
    const ctx = document.getElementById('occupancyChart').getContext('2d');
    
    if (occupancyChart) {
        occupancyChart.destroy();
    }
    
    if (!data.occupancy || data.occupancy.length === 0) {
        occupancyChart = createEmptyChart(ctx, 'No occupancy data available');
        return;
    }
    
    let totalOccupied = 0, totalVacant = 0;
    data.occupancy.forEach(lot => {
        totalOccupied += lot.occupied;
        totalVacant += lot.available;
    });
    
    occupancyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Occupied', 'Vacant'],
            datasets: [{
                label: 'Number of Spots',
                data: [totalOccupied, totalVacant],
                backgroundColor: ['rgba(220, 53, 69, 0.8)', 'rgba(40, 167, 69, 0.8)'],
                borderColor: ['rgba(220, 53, 69, 1)', 'rgba(40, 167, 69, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = totalOccupied + totalVacant;
                            const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed.y} spots (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function updateUtilizationChart(data) {
    const ctx = document.getElementById('utilizationChart').getContext('2d');
    
    if (utilizationChart) {
        utilizationChart.destroy();
    }
    
    if (!data.occupancy || data.occupancy.length === 0) {
        utilizationChart = createEmptyChart(ctx, 'No utilization data available');
        return;
    }
    
    const lotNames = data.occupancy.map(lot => lot.location_name);
    const utilizationRates = data.occupancy.map(lot => {
        const total = lot.occupied + lot.available;
        return total > 0 ? ((lot.occupied / total) * 100).toFixed(1) : 0;
    });
    
    utilizationChart = new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: lotNames,
            datasets: [{
                label: 'Utilization Rate (%)',
                data: utilizationRates,
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed.x}% utilized`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function updateActivityChart(data) {
    const ctx = document.getElementById('activityChart').getContext('2d');
    
    if (activityChart) {
        activityChart.destroy();
    }
    
    // Generate mock daily activity data (in a real app, this would come from the API)
    const last7Days = [];
    const activityData = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        last7Days.push(date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }));
        // Mock data - in real app, calculate from actual reservations
        activityData.push(Math.floor(Math.random() * 20) + 5);
    }
    
    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: last7Days,
            datasets: [{
                label: 'Daily Reservations',
                data: activityData,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createEmptyChart(ctx, message) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['No Data'],
            datasets: [{
                data: [0],
                backgroundColor: 'rgba(201, 203, 207, 0.8)',
                borderColor: 'rgba(201, 203, 207, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                y: { display: false },
                x: { display: false }
            }
        }
    });
}

function showEmptyCharts() {
    const chartIds = ['revenueChart', 'occupancyChart', 'utilizationChart', 'activityChart'];
    
    chartIds.forEach(chartId => {
        const ctx = document.getElementById(chartId).getContext('2d');
        createEmptyChart(ctx, 'No data available');
    });
    
    // Reset statistics
    document.getElementById('totalLots').textContent = '0';
    document.getElementById('totalRevenue').textContent = '₹0';
    document.getElementById('totalOccupied').textContent = '0';
    document.getElementById('totalVacant').textContent = '0';
}

function generateColors(count) {
    const colors = [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 205, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159, 64, 0.8)',
        'rgba(199, 199, 199, 0.8)',
        'rgba(83, 102, 255, 0.8)'
    ];
    
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}