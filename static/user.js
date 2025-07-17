// user.js

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
        });
}

function reserveSpot() {
    const userId = localStorage.getItem('user_id');
    const lotId = document.getElementById('lotSelect').value;
    const vehicleNumber = document.getElementById('vehicleNumber').value.trim().toUpperCase();

    // Vehicle number validation: GJ(01-33)(A-Z)(A-Z)(0001-9999, not 0000)
    const vehicleRegex = /^GJ(0[1-9]|1[0-9]|2[0-9]|3[0-3])[A-Z]{2}(?!0000)\d{4}$/;
    if (!lotId || lotId === '__search__') {
        alert('Please select a parking lot');
        return;
    }
    if (!vehicleNumber) {
        alert('Please enter your vehicle number');
        return;
    }
    if (!vehicleRegex.test(vehicleNumber)) {
        alert('Vehicle number must be in format: GJ01AA0001 to GJ33ZZ9999 (not 0000)');
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
            loadLots();
        }
    })
    .catch(error => {
        document.getElementById('reserveMsg').textContent = 'Error reserving spot. Please try again.';
    });
}

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
            loadLots();
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