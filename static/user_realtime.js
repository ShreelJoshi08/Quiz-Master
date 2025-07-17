// user_realtime.js - Enhanced with WebSocket real-time features

let socket;
let userId;
let userName;

document.addEventListener('DOMContentLoaded', function() {
    // Get user info from localStorage
    userId = localStorage.getItem('user_id');
    userName = localStorage.getItem('user_name');
    
    if (userName) document.getElementById('userName').textContent = userName;
    if (!userId) {
        window.location.href = '/';
        return;
    }
    
    // Initialize WebSocket connection
    initializeSocket();
    
    // Load initial data
    loadLots();
    loadSummary();
    checkActiveReservation();

    // Event listeners
    document.getElementById('reserveBtn').onclick = reserveSpot;
    document.getElementById('vacateBtn').onclick = vacateSpot;
    document.getElementById('logoutBtn').onclick = function() {
        if (socket) {
            socket.emit('leave_user');
            socket.disconnect();
        }
        localStorage.clear();
        window.location.href = '/';
    };

    // Search parking lots
    const searchBtn = document.getElementById('searchLotBtn');
    if (searchBtn) {
        searchBtn.onclick = function() {
            const type = document.getElementById('searchType').value;
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) {
                showNotification('Please enter a search term', 'warning');
                return;
            }
            const params = new URLSearchParams();
            if (type === 'name') params.append('name', query);
            else if (type === 'address') params.append('location', query);
            else if (type === 'pin_code') params.append('pincode', query);
            fetch(`/api/user/lots/search?${params.toString()}`)
                .then(res => res.json())
                .then(data => {
                    const resultsDiv = document.getElementById('searchResults');
                    resultsDiv.innerHTML = '';
                    if (data.lots && data.lots.length > 0) {
                        data.lots.forEach(lot => {
                            const card = document.createElement('div');
                            card.className = 'card mb-2';
                            card.innerHTML = `
                                <div class="card-body">
                                    <h5 class="card-title">${lot.location_name}</h5>
                                    <p class="card-text mb-1"><b>Address:</b> ${lot.address}</p>
                                    <p class="card-text mb-1"><b>Pin Code:</b> ${lot.pin_code}</p>
                                    <p class="card-text mb-1"><b>Price:</b> ₹${lot.price}</p>
                                    <p class="card-text mb-2"><b>Available Spots:</b> ${lot.available_spots}</p>
                                    <button class="btn btn-success btn-sm" onclick="selectLotForReservation(${lot.id})">Select This Lot</button>
                                </div>
                            `;
                            resultsDiv.appendChild(card);
                        });
                    } else {
                        resultsDiv.innerHTML = '<div class="text-muted">No parking lots found for your search.</div>';
                    }
                })
                .catch(() => {
                    document.getElementById('searchResults').innerHTML = '<div class="text-danger">Error searching lots.</div>';
                });
        };
    }
});

window.selectLotForReservation = function(lotId) {
    const lotSelect = document.getElementById('lotSelect');
    if (lotSelect) {
        lotSelect.value = lotId;
        showNotification('Lot selected. You can now reserve a spot.', 'success');
        // Scroll to reserve section
        const reserveSection = document.getElementById('reserveSection');
        if (reserveSection) reserveSection.scrollIntoView({ behavior: 'smooth' });
    }
};

function initializeSocket() {
    // Connect to WebSocket server
    socket = io();
    
    // Join user room
    socket.emit('join_user', { user_id: userId });
    
    // Handle real-time updates
    socket.on('availability_update', function(data) {
        updateLotsAvailability(data);
    });
    
    socket.on('spot_reserved', function(data) {
        showNotification(`Spot ${data.spot_id} has been reserved by another user`, 'warning');
        loadLots(); // Refresh lots data
    });
    
    socket.on('spot_vacated', function(data) {
        showNotification(`Spot ${data.spot_id} is now available!`, 'success');
        loadLots(); // Refresh lots data
    });
    
    socket.on('spots_available', function(data) {
        showNotification(`🎉 ${data.message} (${data.available_spots} spots available)`, 'success');
        loadLots(); // Refresh lots data
    });
    
    socket.on('spots_full', function(data) {
        showNotification(`⚠️ ${data.message}`, 'warning');
        loadLots(); // Refresh lots data
    });
    
    socket.on('new_lot_added', function(data) {
        showNotification(`🏢 New parking lot added: ${data.location_name} (${data.max_spots} spots)`, 'info');
        loadLots(); // Refresh lots data
    });
    
    socket.on('lot_deleted', function(data) {
        showNotification(`🗑️ A parking lot has been removed`, 'warning');
        loadLots(); // Refresh lots data
    });
    
    socket.on('connect', function() {
        console.log('Connected to real-time server');
        showNotification('Connected to real-time updates', 'info');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from real-time server');
        showNotification('Disconnected from real-time updates', 'error');
    });
}

function updateLotsAvailability(availabilityData) {
    const lotSelect = document.getElementById('lotSelect');
    const options = lotSelect.options;
    
    for (let i = 0; i < options.length; i++) {
        const option = options[i];
        if (option.value && option.value !== '__search__') {
            const lotId = parseInt(option.value);
            if (availabilityData[lotId] !== undefined) {
                const availableSpots = availabilityData[lotId];
                const lotName = option.textContent.split(' (')[0];
                option.textContent = `${lotName} (${availableSpots} available)`;
                
                // Highlight if spots became available
                if (availableSpots > 0) {
                    option.style.color = '#28a745';
                    option.style.fontWeight = 'bold';
                } else {
                    option.style.color = '#dc3545';
                }
            }
        }
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function loadLots(lotsData) {
    const lotSelect = document.getElementById('lotSelect');
    lotSelect.innerHTML = '';
    
    // Add 'Search Lots' option
    const searchOpt = document.createElement('option');
    searchOpt.value = '__search__';
    searchOpt.textContent = '🔍 Search Lots...';
    lotSelect.appendChild(searchOpt);
    
    if (lotsData) {
        lotsData.forEach(lot => {
            const opt = document.createElement('option');
            opt.value = lot.id;
            opt.textContent = `${lot.location_name} (${lot.available_spots} available)`;
            if (lot.available_spots > 0) {
                opt.style.color = '#28a745';
            }
            lotSelect.appendChild(opt);
        });
    } else {
        // Default: load all lots
        fetch('/api/user/lots')
            .then(res => res.json())
            .then(data => {
                data.lots.forEach(lot => {
                    const opt = document.createElement('option');
                    opt.value = lot.id;
                    opt.textContent = `${lot.location_name} (${lot.available_spots} available)`;
                    if (lot.available_spots > 0) {
                        opt.style.color = '#28a745';
                    }
                    lotSelect.appendChild(opt);
                });
            })
            .catch(error => {
                showNotification('Error loading parking lots', 'error');
            });
    }
    
    lotSelect.onchange = function() {
        if (this.value === '__search__') {
            searchLotsPrompt();
        }
    };
}

function searchLotsPrompt() {
    const location = prompt('Enter location (leave blank to skip):') || '';
    const pincode = prompt('Enter pincode (leave blank to skip):') || '';
    const name = prompt('Enter lot name (leave blank to skip):') || '';
    const availableOnly = confirm('Show only lots with available spots?');
    
    // If all blank and not filtering, reload all
    if (!location && !pincode && !name && !availableOnly) {
        loadLots();
        return;
    }
    
    const params = new URLSearchParams();
    if (location) params.append('location', location);
    if (pincode) params.append('pincode', pincode);
    if (name) params.append('name', name);
    if (availableOnly) params.append('available_only', 'true');
    
    fetch(`/api/user/lots/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            loadLots(data.lots);
        })
        .catch(error => {
            showNotification('Error searching lots', 'error');
        });
}

function reserveSpot() {
    const lotId = document.getElementById('lotSelect').value;
    const vehicleNumber = document.getElementById('vehicleNumber').value.trim().toUpperCase();

    // Vehicle number validation: GJ(01-33)(A-Z)(A-Z)(0001-9999, not 0000)
    const vehicleRegex = /^GJ(0[1-9]|1[0-9]|2[0-9]|3[0-3])[A-Z]{2}(?!0000)\d{4}$/;
    if (!lotId || lotId === '__search__') {
        showNotification('Please select a parking lot', 'warning');
        return;
    }
    if (!vehicleNumber) {
        showNotification('Please enter your vehicle number', 'warning');
        return;
    }
    if (!vehicleRegex.test(vehicleNumber)) {
        showNotification('Vehicle number must be in format: GJ01AA0001 to GJ33ZZ9999 (not 0000)', 'error');
        return;
    }
    
    // Show loading state
    const reserveBtn = document.getElementById('reserveBtn');
    const originalText = reserveBtn.textContent;
    reserveBtn.textContent = 'Reserving...';
    reserveBtn.disabled = true;
    
    fetch('/api/user/reserve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            user_id: userId, 
            lot_id: lotId, 
            vehicle_number: vehicleNumber 
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            showNotification('Spot reserved successfully!', 'success');
            document.getElementById('vehicleNumber').value = '';
            checkActiveReservation();
            loadSummary();
            loadLots();
        }
    })
    .catch(error => {
        showNotification('Error reserving spot. Please try again.', 'error');
    })
    .finally(() => {
        reserveBtn.textContent = originalText;
        reserveBtn.disabled = false;
    });
}

function checkActiveReservation() {
    fetch(`/api/user/summary/${userId}`)
        .then(res => res.json())
        .then(data => {
            const active = data.reservations.find(r => !r.time_out);
            const vacateSection = document.getElementById('vacateSection');
            const reserveSection = document.getElementById('reserveSection');
            
            if (active) {
                vacateSection.style.display = '';
                document.getElementById('currentReservation').innerHTML = `
                    <div class="alert alert-info">
                        <strong>Current Reservation:</strong><br>
                        <b>Lot:</b> ${active.lot_name}<br>
                        <b>Spot:</b> ${active.spot}<br>
                        <b>Vehicle:</b> ${active.vehicle_number || 'N/A'}<br>
                        <b>Time In:</b> ${active.time_in}
                    </div>
                `;
                reserveSection.style.display = 'none';
            } else {
                vacateSection.style.display = 'none';
                reserveSection.style.display = '';
            }
        })
        .catch(error => {
            showNotification('Error checking reservation status', 'error');
        });
}

function vacateSpot() {
    const vacateBtn = document.getElementById('vacateBtn');
    const originalText = vacateBtn.textContent;
    vacateBtn.textContent = 'Vacating...';
    vacateBtn.disabled = true;

    // Ensure userId is present and valid
    if (!userId) {
        showNotification('User session expired. Please log in again.', 'error');
        setTimeout(() => {
            localStorage.clear();
            window.location.href = '/';
        }, 1500);
        vacateBtn.textContent = originalText;
        vacateBtn.disabled = false;
        return;
    }
    
    fetch('/api/user/vacate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            // Show backend error details if available
            showNotification(data.error + (data.details ? ': ' + data.details : ''), 'error');
        } else {
            showNotification('Spot vacated successfully!', 'success');
            checkActiveReservation();
            loadSummary();
            loadLots();
        }
    })
    .catch(error => {
        showNotification('Error vacating spot. Please try again.', 'error');
    })
    .finally(() => {
        vacateBtn.textContent = originalText;
        vacateBtn.disabled = false;
    });
}

function loadSummary() {
    fetch(`/api/user/summary/${userId}`)
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('summaryTableBody');
            tbody.innerHTML = '';
            
            if (data.reservations.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No parking history found</td></tr>';
                return;
            }
            
            data.reservations.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${r.lot_name}</td>
                    <td>${r.spot}</td>
                    <td>${r.vehicle_number || 'N/A'}</td>
                    <td>${r.time_in}</td>
                    <td>${r.time_out || '-'}</td>
                    <td>${r.time_out ? calculateDuration(r.time_in, r.time_out) : '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            showNotification('Error loading parking history', 'error');
        });
}

function calculateDuration(timeIn, timeOut) {
    const start = new Date(timeIn);
    const end = new Date(timeOut);
    const diff = end - start;
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Auto-refresh data every 30 seconds
setInterval(() => {
    if (userId) {
        loadLots();
        checkActiveReservation();
    }
}, 30000); 