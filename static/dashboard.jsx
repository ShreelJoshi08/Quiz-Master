import React from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import "./styles.css";

const ParkingLot = ({ title, totalSpots, occupied }) => {
  const spots = Array.from({ length: totalSpots }, (_, i) => {
    const row = String.fromCharCode(65 + Math.floor(i / 5));
    const col = (i % 5) + 1;
    const name = `${row}${col}`;
    const isOccupied = occupied.includes(name);
    return (
      <div className="col-2" key={name}>
        <div className={`spot ${isOccupied ? "occupied" : ""}`}>{name}</div>
      </div>
    );
  });

  return (
    <div className="col-md-6 mb-3">
      <div className="card">
        <div className="card-header bg-warning text-white d-flex justify-content-between">
          <span>{title}</span>
          <span>Total Spots: {totalSpots}</span>
        </div>
        <div className="card-body">
          <div className="text-muted mb-2">
            Occupied: {occupied.length}/{totalSpots}
          </div>
          <div className="parking-grid">
            <div className="row g-1">{spots}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  return (
    <div className="container-fluid p-0">
      <header className="bg-light border-bottom">
        <div className="container-fluid">
          <div className="row py-2 align-items-center">
            <div className="col-md-6">
              <div className="welcome-text text-success">Welcome to Admin</div>
            </div>
            <div className="col-md-6">
              <nav className="navbar navbar-expand navbar-light">
                <div className="navbar-nav ms-auto">
                  <a className="nav-link active" href="#">Home</a>
                  <a className="nav-link" href="#">Users</a>
                  <a className="nav-link" href="#">Search</a>
                  <a className="nav-link" href="#">Summary</a>
                  <a className="nav-link" href="#">Logout</a>
                  <a className="nav-link text-success" href="#">Edit Profile</a>
                </div>
              </nav>
            </div>
          </div>
        </div>
      </header>

      <main className="container-fluid mt-4">
        <div className="row mb-3">
          <div className="col-12">
            <h5 className="text-primary">Parking Lots</h5>
            <div className="parking-lots-container border rounded p-3">
              <div className="row">
                <ParkingLot
                  title="Parking#1"
                  totalSpots={25}
                  occupied={["A1", "A3", "A5", "B2", "B4", "C1", "C3", "C5", "D2", "D4", "E1", "E3", "E5", "C5", "A3", "D2", "B4"]}
                />
                <ParkingLot
                  title="Parking#2"
                  totalSpots={15}
                  occupied={["A1", "A3", "A5", "B2", "B4", "C1", "C3", "C5", "C5"]}
                />
              </div>
              <div className="text-end mt-3">
                <button className="btn btn-info text-white" id="add-lot-btn">
                  <i className="fas fa-plus"></i> Add Lot
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;