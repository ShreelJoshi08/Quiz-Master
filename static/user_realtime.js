// user_realtime.js - Enhanced with WebSocket real-time features

let socket;
let userId;
let userName;
let lastSearchParams = null; // Store last search parameters

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
        refreshLots(); // Refresh lots data maintaining search state
    });
    
    socket.on('spot_vacated', function(data) {
        showNotification(`Spot ${data.spot_id} is now available!`, 'success');
        refreshLots(); // Refresh lots data maintaining search state
    });
    
    socket.on('spots_available', function(data) {
        showNotification(`🎉 ${data.message} (${data.available_spots} spots available)`, 'success');
        refreshLots(); // Refresh lots data maintaining search state
    });
    
    socket.on('spots_full', function(data) {
        showNotification(`⚠️ ${data.message}`, 'warning');
        refreshLots(); // Refresh lots data maintaining search state
    });
    
    socket.on('new_lot_added', function(data) {
        showNotification(`🏢 New parking lot added: ${data.location_name} (${data.max_spots} spots)`, 'info');
        refreshLots(); // Refresh lots data maintaining search state
    });
    
    socket.on('lot_deleted', function(data) {
        showNotification(`🗑️ A parking lot has been removed`, 'warning');
        refreshLots(); // Refresh lots data maintaining search state
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

// New function to refresh lots with current search or load all
function refreshLots() {
    if (lastSearchParams) {
        // If we have search parameters, refresh the search results
        fetch(`/api/user/lots/search?${lastSearchParams.toString()}`)
            .then(res => res.json())
            .then(data => {
                loadLots(data.lots);
            })
            .catch(error => {
                console.error('Error refreshing search results:', error);
                showNotification('Error refreshing search results', 'error');
                // Fallback to loading all lots
                loadLots();
            });
    } else {
        // No search active, load all lots
        loadLots();
    }
}

function searchLotsPrompt() {
    const location = prompt('Enter location (leave blank to skip):') || '';
    const pincode = prompt('Enter pincode (leave blank to skip):') || '';
    const name = prompt('Enter lot name (leave blank to skip):') || '';
    const availableOnly = confirm('Show only lots with available spots?');
    
    // If all blank and not filtering, clear search and reload all
    if (!location && !pincode && !name && !availableOnly) {
        lastSearchParams = null; // Clear search parameters
        loadLots();
        return;
    }
    
    const params = new URLSearchParams();
    if (location) params.append('location', location);
    if (pincode) params.append('pincode', pincode);
    if (name) params.append('name', name);
    if (availableOnly) params.append('available_only', 'true');
    
    // Store search parameters for future refreshes
    lastSearchParams = params;
    
    fetch(`/api/user/lots/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            loadLots(data.lots);
            showNotification(`Found ${data.lots.length} parking lot(s) matching your search`, 'info');
        })
        .catch(error => {
            showNotification('Error searching lots', 'error');
        });
}

function reserveSpot() {
    const userId = localStorage.getItem('user_id');
    const lotId = document.getElementById('lotSelect').value;
    const vehicleNumber = document.getElementById('vehicleNumber').value.trim().toUpperCase();

    // List of valid state and UT codes
    const stateCodes = [
        "AN","AP","AR","AS","BR","CH","CG","DD","DL","DN","GA","GJ","HP","HR","JH",
        "JK","KA","KL","LA","LD","MH","ML","MN","MP","MZ","NL","OD","PB","PY","RJ",
        "SK","TN","TS","TR","UP","UK","WB"
    ];
    
    // Create dynamic regex for state codes
    const stateRegex = stateCodes.join("|");

    // Comprehensive Indian vehicle number validation
    const vehiclePatterns = [
        // Civilian vehicles (PAN India, strict state code check)
        new RegExp(`^(${stateRegex})[ -]?(0[1-9]|[1-9][0-9])[ -]?[A-Z]{1,3}[ -]?(?!0000)[0-9]{1,4}$`),

        // Temporary registration: TR/TC
        /^TR[ -]?(0[1-9]|[1-9][0-9])[ -]?TC[ -]?[0-9]{1,4}$/i,

        // Diplomatic / Consular Corps
        /^CC[ -]?[0-9]{1,3}[ -]?[0-9]{1,4}$/,
        /^DC[ -]?[0-9]{1,3}[ -]?[0-9]{1,4}$/i,

        // Military plates
        /^[0-9]{2}[A-Z]{1}[0-9]{1,6}[A-Z]{1}$/,

        // Vintage
        new RegExp(`^(${stateRegex})[ -]?(0[1-9]|[1-9][0-9])[ -]?[A-Z]{2}[ -]?[0-9]{4}$`)
    ];

    if (!lotId || lotId === '__search__') {
        alert('Please select a parking lot');
        return;
    }
    if (!vehicleNumber) {
        alert('Please enter your vehicle number');
        return;
    }

    // Validate against all patterns
    const isValidFormat = vehiclePatterns.some(pattern => pattern.test(vehicleNumber));
    if (!isValidFormat) {
    alert(
        "❌ Invalid Vehicle Number!\n\n" +
        "Please enter a valid Indian vehicle number in the correct format.\n\n" +
        "✔ Examples:\n" +
        "   • MH12AB1234\n" +
        "   • DL8CAF2023\n" +
        "   • TR01TC1234 (Temporary)\n" +
        "   • CC12 1234 (Diplomatic)\n\n" +
        "👉 Make sure:\n" +
        "   • State code (e.g., MH, DL, GJ) is correct\n" +
        "   • RTO code is between 01-99\n" +
        "   • Vehicle number is 0001-9999 (not 0000)\n\n" +
        "Please try again."
    );
    return;
}

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
            document.getElementById('reserveMsg').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else {
            document.getElementById('reserveMsg').innerHTML = `<div class="alert alert-success">Spot reserved successfully!</div>`;
            document.getElementById('vehicleNumber').value = '';
            checkActiveReservation();
            loadSummary();
            loadLots();
            
            // Clear message after 3 seconds
            setTimeout(() => {
                document.getElementById('reserveMsg').innerHTML = '';
            }, 3000);
        }
    })
    .catch(error => {
        document.getElementById('reserveMsg').innerHTML = `<div class="alert alert-danger">Error reserving spot. Please try again.</div>`;
    });
}


function checkActiveReservation() {
    fetch(`/api/user/summary/${userId}`)
        .then(res => res.json())
        .then(data => {
            const activeReservations = data.reservations.filter(r => !r.time_out);
            const activeReservationsSection = document.getElementById('activeReservationsSection');
            const reserveSection = document.getElementById('reserveSection');
            
            if (activeReservations.length > 0) {
                activeReservationsSection.style.display = '';
                let reservationsHtml = `
                    <div class="alert alert-info mb-3">
                        <strong>Your Active Reservations:</strong>
                    </div>
                `;
                
                activeReservations.forEach((reservation, index) => {
                    reservationsHtml += `
                        <div class="reservation-card">
                            <div class="row align-items-center">
                                <div class="col-md-8 reservation-info">
                                    <p><strong>Lot:</strong> ${reservation.lot_name}</p>
                                    <p><strong>Spot:</strong> ${reservation.spot}</p>
                                    <p><strong>Vehicle:</strong> ${reservation.vehicle_number || 'N/A'}</p>
                                    <p class="mb-0"><strong>Time In:</strong> ${reservation.time_in}</p>
                                </div>
                                <div class="col-md-4 text-end">
                                    <button class="btn btn-danger vacate-btn" data-spot-id="${reservation.spot_id}" data-vehicle-number="${reservation.vehicle_number}">
                                        Vacate This Spot
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                document.getElementById('activeReservationsList').innerHTML = reservationsHtml;
                
                // Add event listeners to vacate buttons
                document.querySelectorAll('.vacate-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const spotId = this.getAttribute('data-spot-id');
                        const vehicleNumber = this.getAttribute('data-vehicle-number');
                        
                        // Add loading state
                        const originalText = this.textContent;
                        this.textContent = 'Vacating...';
                        this.disabled = true;
                        
                        vacateSpecificSpot(spotId, vehicleNumber).finally(() => {
                            this.textContent = originalText;
                            this.disabled = false;
                        });
                    });
                });
                
                // Keep reservation section visible - users can book more spots
                reserveSection.style.display = '';
            } else {
                activeReservationsSection.style.display = 'none';
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

function vacateSpecificSpot(spotId, vehicleNumber) {
    console.log('vacateSpecificSpot called with:', spotId, vehicleNumber);
    
    if (!confirm(`Are you sure you want to vacate the spot for vehicle ${vehicleNumber}?`)) {
        return;
    }
    
    // Ensure userId is present and valid
    if (!userId) {
        showNotification('User session expired. Please log in again.', 'error');
        setTimeout(() => {
            localStorage.clear();
            window.location.href = '/';
        }, 1500);
        return;
    }
    
    console.log('Making API call to vacate spot:', spotId, 'for vehicle:', vehicleNumber);
    
    fetch('/api/user/vacate-specific', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            user_id: userId, 
            spot_id: spotId,
            vehicle_number: vehicleNumber 
        })
    })
    .then(res => {
        console.log('API response status:', res.status);
        return res.json();
    })
    .then(data => {
        console.log('API response data:', data);
        if (data.error) {
            showNotification(data.error + (data.details ? ': ' + data.details : ''), 'error');
        } else {
            showNotification(`Spot vacated successfully for vehicle ${vehicleNumber}!`, 'success');
            checkActiveReservation();
            loadSummary();
            loadLots();
        }
    })
    .catch(error => {
        console.error('Error vacating spot:', error);
        showNotification('Error vacating spot. Please try again.', 'error');
    });
}

// Make function globally available
window.vacateSpecificSpot = vacateSpecificSpot;

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