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
        alert('Invalid vehicle number.\nExamples: MH12AB1234, DL8CAF2023, TR01TC1234, CC12 1234');
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
            document.getElementById('reserveMsg').textContent = data.error;
        } else {
            document.getElementById('reserveMsg').textContent = 'Spot reserved successfully!';
            document.getElementById('vehicleNumber').value = '';
            checkActiveReservation();
            loadSummary();
            refreshLots(); // Use refreshLots to maintain search state
        }
    })
    .catch(error => {
        document.getElementById('reserveMsg').textContent = 'Error reserving spot. Please try again.';
    });
}

// user.js

// Global variable to store last search parameters
let lastSearchParams = null;

document.addEventListener('DOMContentLoaded', function() {
    // Assume user_id and user_name are stored in localStorage after login
    const userId = localStorage.getItem('user_id');
    const userName = localStorage.getItem('user_name');
    if (userName) document.getElementById('userName').textContent = userName;
    if (!userId) {
        window.location.href = '/';
          return;
        }
    loadLots();
    loadSummary();
    checkActiveReservation();

    document.getElementById('reserveBtn').onclick = reserveSpot;
    document.getElementById('vacateBtn').onclick = vacateSpot;
    document.getElementById('logoutBtn').onclick = function() {
        localStorage.clear();
        window.location.href = '/';
    };
});

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
                    lotSelect.appendChild(opt);
                });
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
        })
        .catch(error => {
            console.error('Search error:', error);
            alert('Error searching lots. Please try again.');
        });
}

// function reserveSpot() {
//     const userId = localStorage.getItem('user_id');
//     const lotId = document.getElementById('lotSelect').value;
//     const vehicleNumber = document.getElementById('vehicleNumber').value.trim().toUpperCase();

//     // Simplified Indian vehicle number validation pattern to accept all states:
//     // Format: Two letters (state), 1-2 digits (RTO), 1-2 letters, 4 digits
//     const vehiclePatterns = [
//         /^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$/  // e.g. GJ01AB1234, MH12CD5678, DL8CAF2023
//     ];
    
//     if (!lotId || lotId === '__search__') {
//         alert('Please select a parking lot');
//         return;
//     }
//     if (!vehicleNumber) {
//         alert('Please enter your vehicle number');
//         return;
//     }
    
//     // Check if vehicle number matches any Indian format
//     const isValidFormat = vehiclePatterns.some(pattern => pattern.test(vehicleNumber));
//     if (!isValidFormat) {
//         // Remove or simplify the alert message as per user request
//         // alert('Please enter a valid Indian vehicle number (e.g., GJ01AB1234, MH12CD5678, DL8CAF2023, etc.)');
//         // Instead of alert, show message in reserveMsg element
//         document.getElementById('reserveMsg').textContent = 'Invalid vehicle number format. Please check and try again.';
//         return;
//     }
    
//     fetch('/api/user/reserve', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ 
//             user_id: userId, 
//             lot_id: lotId, 
//             vehicle_number: vehicleNumber 
//         })
//     })
//     .then(res => res.json())
//     .then(data => {
//         if (data.error) {
//             document.getElementById('reserveMsg').textContent = data.error;
//         } else {
//             document.getElementById('reserveMsg').textContent = 'Spot reserved successfully!';
//             document.getElementById('vehicleNumber').value = '';
//             checkActiveReservation();
//             loadSummary();
//             loadLots();
//         }
//     })
//     .catch(error => {
//         document.getElementById('reserveMsg').textContent = 'Error reserving spot. Please try again.';
//     });
// }

function checkActiveReservation() {
    const userId = localStorage.getItem('user_id');
    fetch(`/api/user/summary/${userId}`)
        .then(res => res.json())
        .then(data => {
            const active = data.reservations.find(r => !r.time_out);
            const vacateSection = document.getElementById('vacateSection');
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
                document.getElementById('reserveSection').style.display = 'none';
            } else {
                vacateSection.style.display = 'none';
                document.getElementById('reserveSection').style.display = '';
            }
      });
    }
  
function vacateSpot() {
    const userId = localStorage.getItem('user_id');
    fetch('/api/user/vacate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById('vacateMsg').textContent = data.error;
        } else {
            document.getElementById('vacateMsg').textContent = 'Spot vacated!';
            checkActiveReservation();
            loadSummary();
            refreshLots(); // Use refreshLots to maintain search state
        }
    });
}

function loadSummary() {
    const userId = localStorage.getItem('user_id');
    fetch(`/api/user/summary/${userId}`)
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('summaryTableBody');
            tbody.innerHTML = '';
            data.reservations.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${r.lot_name}</td>
                    <td>${r.spot}</td>
                    <td>${r.vehicle_number || 'N/A'}</td>
                    <td>${r.time_in}</td>
                    <td>${r.time_out || '-'}</td>
                    <td>${r.duration || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        });
}