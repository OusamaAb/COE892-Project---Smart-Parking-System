/**
 * ParkingLot.jsx — Main lot view with sensor-driven microservice flow.
 *
 * Flow:
 *  1. User clicks "Add Car" → drivable car spawns at entrance.
 *  2. Car overlaps a FREE bay → POST /sensor-event {car_entered}
 *     → sensor_service marks spot occupied instantly.
 *  3. Car leaves the bay → POST /sensor-event {car_left}
 *     → if no reservation, sensor_service marks spot free.
 *  4. While sitting in a bay, press Space → parking modal opens
 *     (hours + rate). Confirm → reservation created, spot stays
 *     permanently occupied. Cancel → keep driving, spot freed on leave.
 *  5. Click an occupied spot (not driving) → release modal
 *     → DELETE /reservations/{id} → spot freed.
 */

import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  fetchSpots,
  fetchLotClock,
  sendSensorEvent,
  createReservation,
  releaseReservation,
  checkSpotReservation,
} from "../api/parkingApi";
import ParkingSpot from "./ParkingSpot";
import DrivableCar from "./DrivableCar";

const SECTIONS = [
  { top: "A", bottom: "B" },
  { top: "C", bottom: "D" },
];
const HOUR_OPTIONS = [1, 2, 3, 4, 5, 6, 8, 12, 24];

/** Lot-time ISO (naive) + hours → "h:mm AM/PM" leave-by string */
function leaveByFromLotIso(lotIso, hours) {
  if (!lotIso || !hours) return "";
  const d = new Date(lotIso.includes("T") ? lotIso : lotIso.replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return "";
  const end = new Date(d.getTime() + hours * 3600000);
  return end.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function ParkingLot() {
  const [spots, setSpots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [drivingMode, setDrivingMode] = useState(false);
  const [sensorSpotId, setSensorSpotId] = useState(null);

  const [parkModal, setParkModal] = useState(null);
  const [selectedHours, setSelectedHours] = useState(1);

  const [releaseModal, setReleaseModal] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [lotClock, setLotClock] = useState(null);

  const lotRef = useRef(null);

  /* Tracks which spot the sensor currently occupies (backend-side) */
  const sensorOccupiedRef = useRef(null);
  /* Guards against overlapping async sensor flows */
  const sensorBusyRef = useRef(false);

  /* ---- Data loading ---------------------------------------------------- */

  /** Backend already counts our car in a bay → use actual occupancy; else +1 preview */
  function pricingExtraOccupied() {
    return sensorOccupiedRef.current != null ? 0 : 1;
  }

  const loadSpots = useCallback(async () => {
    try {
      const data = await fetchSpots(pricingExtraOccupied());
      setSpots(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch spots:", err);
      setError("Could not load parking data. Are all services running?");
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSpots(); }, [loadSpots]);

  /* Poll lot clock + spots so auto-expired cars disappear without refresh */
  useEffect(() => {
    async function poll() {
      try {
        const lc = await fetchLotClock();
        setLotClock(lc);
        await loadSpots();
      } catch (e) {
        console.error("lot-clock poll:", e);
      }
    }
    poll();
    const id = setInterval(poll, 8000);
    return () => clearInterval(id);
  }, [loadSpots]);

  /* ---- Helpers --------------------------------------------------------- */

  function spotsForRow(letter) {
    return spots.filter((s) => s.label.startsWith(letter));
  }

  const freeCount     = spots.filter((s) => s.status === "free").length;
  const occupiedCount = spots.filter((s) => s.status === "occupied").length;
  const currentPrice  = spots.length > 0 ? spots[0].price : 0;

  /* ---- Sensor change handler (from DrivableCar) ------------------------ */

  async function handleSensorChange(newSpotId) {
    setSensorSpotId(newSpotId);

    const oldSpotId = sensorOccupiedRef.current;
    if (newSpotId === oldSpotId) return;

    if (sensorBusyRef.current) return;
    sensorBusyRef.current = true;

    try {
      /* Car LEFT a spot it was physically in */
      if (oldSpotId !== null) {
        sensorOccupiedRef.current = null;
        try {
          await sendSensorEvent(oldSpotId, "car_left");
        } catch (e) { console.error("sensor car_left failed:", e); }
      }

      /* Car ENTERED a new spot */
      if (newSpotId !== null) {
        const freshSpots = await fetchSpots(pricingExtraOccupied());
        setSpots(freshSpots);
        const spot = freshSpots.find((s) => s.id === newSpotId);

        if (spot && spot.status === "free") {
          sensorOccupiedRef.current = newSpotId;
          try {
            await sendSensorEvent(newSpotId, "car_entered");
          } catch (e) { console.error("sensor car_entered failed:", e); }

          const updatedSpots = await fetchSpots(pricingExtraOccupied());
          setSpots(updatedSpots);
        }
      } else {
        await loadSpots();
      }
    } finally {
      sensorBusyRef.current = false;
    }
  }

  /* ---- Park request (Space pressed while in a bay) -------------------- */

  async function handleParkRequest(spotId) {
    const freshSpots = await fetchSpots(pricingExtraOccupied());
    setSpots(freshSpots);
    const spot = freshSpots.find((s) => s.id === spotId);
    if (!spot) return;
    setParkModal(spot);
    setSelectedHours(1);
  }

  /* ---- Parking confirm / cancel --------------------------------------- */

  async function handleParkConfirm() {
    if (!parkModal) return;
    setActionLoading(true);
    try {
      await createReservation(parkModal.id, selectedHours);
      await loadSpots();
      setParkModal(null);
      setDrivingMode(false);
      setSensorSpotId(null);
      sensorOccupiedRef.current = null;
    } catch (err) {
      console.error("Failed to create reservation:", err);
      alert("Something went wrong. Please try again.");
    } finally {
      setActionLoading(false);
    }
  }

  function handleParkCancel() {
    setParkModal(null);
  }

  /* ---- Driving controls ----------------------------------------------- */

  function handleAddCar() {
    setDrivingMode(true);
    setSensorSpotId(null);
    sensorOccupiedRef.current = null;
    loadSpots();
  }

  async function handleDrivingCancel() {
    /* If the car is physically in a spot, send car_left */
    if (sensorOccupiedRef.current !== null) {
      try {
        await sendSensorEvent(sensorOccupiedRef.current, "car_left");
      } catch (e) { console.error("car_left on cancel failed:", e); }
      sensorOccupiedRef.current = null;
      await loadSpots();
    }
    setDrivingMode(false);
    setSensorSpotId(null);
    setParkModal(null);
  }

  /* ---- Release flow (click occupied spot while NOT driving) ----------- */

  async function handleSpotClick(spot) {
    if (drivingMode) return;
    if (spot.status !== "occupied") return;

    /* Check if the spot has a reservation to release */
    try {
      const resData = await checkSpotReservation(spot.id);
      if (resData.has_reservation) {
        setReleaseModal({
          spot,
          reservation: resData.reservation,
        });
      } else {
        setReleaseModal({ spot, reservation: null });
      }
    } catch {
      setReleaseModal({ spot, reservation: null });
    }
  }

  async function handleRelease() {
    if (!releaseModal) return;
    setActionLoading(true);
    try {
      if (releaseModal.reservation) {
        await releaseReservation(releaseModal.reservation.id);
      } else {
        /* No reservation — just send a car_left sensor event to free it */
        await sendSensorEvent(releaseModal.spot.id, "car_left");
      }
      await loadSpots();
      setReleaseModal(null);
    } catch (err) {
      console.error("Failed to release spot:", err);
      alert("Something went wrong. Please try again.");
    } finally {
      setActionLoading(false);
    }
  }

  /* ---- Render --------------------------------------------------------- */

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>Loading parking lot...</p>
      </div>
    );
  }

  if (error) {
    return <p className="status-message error">{error}</p>;
  }

  return (
    <div className="parking-lot-wrapper">
      {/* ---- Stats bar -------------------------------------------------- */}
      <div className="stats-bar">
        <div className="stat">
          <span className="stat-dot free-dot" />
          <span>Available <strong>{freeCount}</strong></span>
        </div>
        <div className="stat">
          <span className="stat-dot occupied-dot" />
          <span>Occupied <strong>{occupiedCount}</strong></span>
        </div>
        <div className="stat price-stat">
          <span>Rate <strong>${currentPrice.toFixed(2)}/hr</strong></span>
        </div>

        {lotClock && (
          <div className="stat lot-clock-stat" title="Simulated lot time (session only). Advances every minute.">
            <span>Lot time <strong>{lotClock.display}</strong></span>
            <span className="lot-clock-hint">
              +{lotClock.sim_minutes_per_tick} min / {lotClock.real_seconds_per_tick}s
            </span>
          </div>
        )}

        {!drivingMode ? (
          <button className="btn add-car-btn" onClick={handleAddCar} disabled={freeCount === 0}>
            + Add Car
          </button>
        ) : (
          <button className="btn exit-drive-btn" onClick={handleDrivingCancel}>
            Cancel Driving
          </button>
        )}
      </div>

      {/* ---- Driving hint ------------------------------------------------ */}
      {drivingMode && !parkModal && (
        <div className="driving-hint">
          Arrow keys / WASD to drive&ensp;·&ensp;Space to park in a spot&ensp;·&ensp;Esc to cancel
        </div>
      )}

      {/* ---- Lot surface ------------------------------------------------ */}
      <div className="lot-surface" ref={lotRef}>
        <div className="lot-entrance">
          <span className="entrance-text">&#9660; ENTRANCE</span>
        </div>

        {SECTIONS.map((sec, i) => (
          <div className="parking-section" key={i}>
            <div className="bay-row facing-down">
              <div className="row-marker">{sec.top}</div>
              <div className="bays">
                {spotsForRow(sec.top).map((spot) => (
                  <ParkingSpot
                    key={spot.id}
                    spot={spot}
                    direction="down"
                    highlighted={sensorSpotId === spot.id}
                    disabled={drivingMode}
                    onClick={handleSpotClick}
                  />
                ))}
              </div>
            </div>
            <div className="driving-lane">
              <span className="lane-arrow">&#10142;</span>
            </div>
            <div className="bay-row facing-up">
              <div className="row-marker">{sec.bottom}</div>
              <div className="bays">
                {spotsForRow(sec.bottom).map((spot) => (
                  <ParkingSpot
                    key={spot.id}
                    spot={spot}
                    direction="up"
                    highlighted={sensorSpotId === spot.id}
                    disabled={drivingMode}
                    onClick={handleSpotClick}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}

        <div className="lot-exit">
          <span className="exit-text">EXIT &#9650;</span>
        </div>

        {/* Drivable car — stays mounted while driving, paused during modal */}
        {drivingMode && (
          <DrivableCar
            lotRef={lotRef}
            paused={!!parkModal}
            onSensorChange={handleSensorChange}
            onPark={handleParkRequest}
            onCancel={handleDrivingCancel}
          />
        )}
      </div>

      {/* ---- Legend ------------------------------------------------------ */}
      <div className="legend">
        <div className="legend-item"><span className="legend-swatch free-swatch" /><span>Available</span></div>
        <div className="legend-item"><span className="legend-swatch occupied-swatch" /><span>Occupied</span></div>
        <div className="legend-item"><span className="legend-swatch sensor-swatch" /><span>Sensor detected</span></div>
      </div>

      {/* ---- Release modal ---------------------------------------------- */}
      {releaseModal && (
        <div className="modal-overlay" onClick={() => setReleaseModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>Release spot {releaseModal.spot.label}?</h2>
            {releaseModal.reservation && (
              <p className="modal-hint">
                Reservation #{releaseModal.reservation.id} —
                {" "}{releaseModal.reservation.hours}hr
                {" "}@ ${releaseModal.reservation.rate}/hr
                {" "}= ${releaseModal.reservation.total}
                {releaseModal.reservation.ends_at_sim_display && (
                  <>
                    <br />
                    Lot leave-by: <strong>{releaseModal.reservation.ends_at_sim_display}</strong>
                  </>
                )}
              </p>
            )}
            <p className="modal-hint">This will free the spot for others.</p>
            <div className="modal-actions">
              <button className="btn btn-cancel" onClick={() => setReleaseModal(null)} disabled={actionLoading}>
                Cancel
              </button>
              <button className="btn btn-release" onClick={handleRelease} disabled={actionLoading}>
                {actionLoading ? "Processing..." : "Release Spot"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ---- Parking modal (Space key while in a bay) -------------------- */}
      {parkModal && (
        <div className="modal-overlay" onClick={handleParkCancel}>
          <div className="modal-card parking-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Park in spot {parkModal.label}</h2>

            <p className="modal-price">
              Rate: <strong>${parkModal.price.toFixed(2)}/hr</strong>
            </p>

            {lotClock?.iso && (
              <p className="modal-hint lot-leave-preview">
                If you confirm, leave by{" "}
                <strong>{leaveByFromLotIso(lotClock.iso, selectedHours)}</strong>
                {" "}lot time ({selectedHours}h from current lot time)
              </p>
            )}

            <p className="modal-subtitle">Select duration</p>
            <div className="hours-picker">
              {HOUR_OPTIONS.map((h) => (
                <button
                  key={h}
                  className={`hour-btn ${selectedHours === h ? "selected" : ""}`}
                  onClick={() => setSelectedHours(h)}
                >
                  {h}h
                </button>
              ))}
            </div>

            <div className="cost-breakdown">
              <span>${parkModal.price.toFixed(2)} × {selectedHours}hr{selectedHours > 1 ? "s" : ""}</span>
              <span className="cost-total">
                = ${(parkModal.price * selectedHours).toFixed(2)}
              </span>
            </div>

            <div className="modal-actions">
              <button className="btn btn-cancel" onClick={handleParkCancel} disabled={actionLoading}>
                Cancel
              </button>
              <button className="btn btn-reserve" onClick={handleParkConfirm} disabled={actionLoading}>
                {actionLoading ? "Parking..." : "Confirm Parking"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ParkingLot;
