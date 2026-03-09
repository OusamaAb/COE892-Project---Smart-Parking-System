/**
 * App.jsx — Root component for the Smart Parking System frontend.
 */

import React from "react";
import ParkingLot from "./components/ParkingLot";
import "./App.css";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-icon">&#127359;</div>
        <h1>Smart Parking System</h1>
        <p>Real-time lot availability &amp; dynamic pricing</p>
      </header>

      <main className="app-main">
        <ParkingLot />
      </main>

      <footer className="app-footer">
        COE892 — Distributed Cloud Computing Project
      </footer>
    </div>
  );
}

export default App;
