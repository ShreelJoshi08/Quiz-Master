// admin_dashboard.js - rewritten for new admin dashboard UI

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching (Bootstrap handles, but we can add logic if needed)
    // Load initial data for Home tab
    loadParkingLots();
    // Users tab
    document.getElementById('users-tab').addEventListener('click', loadUsers);
    // Search tab
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
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
    const data = {
        location_name: document.getElementById('newLotName').value,
        address: document.getElementById('newLotAddress').value,
        pin_code: document.getElementById('newLotPincode').value,
        price: document.getElementById('newLotPrice').value,
        max_spots: document.getElementById('newLotSpots').value
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
    if (confirm('Are you sure you want to delete this parking lot?')) {
        fetch(`/api/admin/lots/${lotId}`, { method: 'DELETE' })
            .then(() => {
                loadParkingLots();
                renderSummaryCharts();
            });
    }
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

function showToast(message) {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-bg-success border-0 show';
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
    const bsToast = new bootstrap.Toast(toast, { delay: 2000 });
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
    const str = document.getElementById('searchString').value;
    fetch(`/api/admin/search?by=${by}&q=${encodeURIComponent(str)}`)
        .then(res => res.json())
        .then(data => {
            const results = document.getElementById('searchResults');
            results.innerHTML = '';
            if (data.results && data.results.length > 0) {
                data.results.forEach(item => {
                    results.innerHTML += `<div class="card mb-2 p-2">${item}</div>`;
                });
            } else {
                results.innerHTML = '<div class="text-muted">No results found.</div>';
            }
        });
}

// --- Summary Charts ---
function renderSummaryCharts() {
    if (window.Chart) {
        fetch('/api/admin/summary?ts=' + Date.now())
            .then(res => res.json())
            .then(data => {
                // Prepare data for charts
                const lot_names = data.revenue.map(lot => lot.location_name);
                const revenues = data.revenue.map(lot => lot.revenue);
                let total_occupied = 0, total_vacant = 0;
                data.occupancy.forEach(lot => {
                    total_occupied += lot.occupied;
                    total_vacant += lot.available;
                });

                // Revenue chart
                const revCtx = document.getElementById('revenueChart').getContext('2d');
                if (window.revenueChart) window.revenueChart.destroy();
                window.revenueChart = new Chart(revCtx, {
                    type: 'doughnut',
                    data: {
                        labels: lot_names,
                        datasets: [{ data: revenues, backgroundColor: ['#1976d2', '#ffc107', '#17a2b8', '#dc3545', '#6c757d', '#28a745', '#fd7e14'] }]
                    },
                    options: { plugins: { legend: { position: 'bottom' } }, cutout: '60%' }
                });

                // Occupancy chart
                const occCtx = document.getElementById('occupancyChart').getContext('2d');
                if (window.occupancyChart) window.occupancyChart.destroy();
                window.occupancyChart = new Chart(occCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Occupied', 'Vacant'],
                        datasets: [{ label: 'Spots', data: [total_occupied, total_vacant], backgroundColor: ['#1976d2', '#17a2b8'] }]
                    },
                    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, precision: 0 } } }
                });
            });
    } else {
        document.getElementById('revenueChart').innerHTML = '<div class="chart-placeholder pie-chart"></div>';
        document.getElementById('occupancyChart').innerHTML = '<div class="chart-placeholder bar-chart"></div>';
    }
}