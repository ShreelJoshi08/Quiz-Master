// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Navigation Links
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const dashboardContent = document.getElementById('dashboard-content');
    const userView = document.querySelector('.user-view');
    const searchView = document.querySelector('.search-view');
    const summaryView = document.querySelector('.summary-view');
    
    // Parking Spots
    const parkingSpots = document.querySelectorAll('.spot');
    
    // Buttons
    const addLotBtn = document.getElementById('add-lot-btn');
    
    // Modals
    const editParkingLotModal = new bootstrap.Modal(document.getElementById('editParkingLotModal'));
    const newParkingLotModal = new bootstrap.Modal(document.getElementById('newParkingLotModal'));
    const viewParkingSpotModal = new bootstrap.Modal(document.getElementById('viewParkingSpotModal'));
    const occupiedSpotDetailsModal = new bootstrap.Modal(document.getElementById('occupiedSpotDetailsModal'));
    
    // Navigation Event Listeners
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const linkText = this.textContent.trim().toLowerCase();
            
            // Reset active state
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Hide all views
            dashboardContent.classList.add('d-none');
            userView.classList.add('d-none');
            searchView.classList.add('d-none');
            summaryView.classList.add('d-none');
            
            // Show selected view
            switch(linkText) {
                case 'home':
                    dashboardContent.classList.remove('d-none');
                    break;
                case 'users':
                    userView.classList.remove('d-none');
                    break;
                case 'search':
                    searchView.classList.remove('d-none');
                    break;
                case 'summary':
                    summaryView.classList.remove('d-none');
                    break;
            }
        });
    });
    
    // Parking Spot Click Events
    parkingSpots.forEach(spot => {
        spot.addEventListener('click', function() {
            if (this.classList.contains('occupied')) {
                occupiedSpotDetailsModal.show();
            } else {
                viewParkingSpotModal.show();
            }
        });
    });
    
    // Add Lot Button Event
    if (addLotBtn) {
        addLotBtn.addEventListener('click', function() {
            newParkingLotModal.show();
        });
    }
    
    // Form Submissions with Validation
    const editParkingLotForm = document.getElementById('editParkingLotForm');
    if (editParkingLotForm) {
        editParkingLotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!this.checkValidity()) {
                e.stopPropagation();
                this.classList.add('was-validated');
                return;
            }
            
            // Handle form submission logic here
            editParkingLotModal.hide();
            alert('Parking lot updated successfully!');
        });
    }
    
    const newParkingLotForm = document.getElementById('newParkingLotForm');
    if (newParkingLotForm) {
        newParkingLotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!this.checkValidity()) {
                e.stopPropagation();
                this.classList.add('was-validated');
                return;
            }
            
            // Handle form submission logic here
            newParkingLotModal.hide();
            alert('New parking lot added successfully!');
        });
    }
    
    const viewParkingSpotForm = document.getElementById('viewParkingSpotForm');
    if (viewParkingSpotForm) {
        viewParkingSpotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!this.checkValidity()) {
                e.stopPropagation();
                this.classList.add('was-validated');
                return;
            }
            
            // Handle form submission logic here
            viewParkingSpotModal.hide();
            alert('Parking spot updated successfully!');
        });
    }
    
    // Simulating clicking on a parking lot to edit
    const parkingLotCards = document.querySelectorAll('.card-header');
    parkingLotCards.forEach(card => {
        card.addEventListener('click', function() {
            editParkingLotModal.show();
        });
    });
});