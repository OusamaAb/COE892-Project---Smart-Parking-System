/**
 * ParkingSpot.jsx — A single parking bay styled to look like a real
 * painted bay seen from above.
 *
 * Three visual states:
 *   FREE       → green price label
 *   SENSOR     → occupied by sensor (car passing through, not reserved yet)
 *               → red pulsing highlight, no parked-car icon
 *   RESERVED   → actually parked/reserved → shows parked car icon
 *
 * Props:
 *   spot        – { id, label, status, price, reserved }
 *   direction   – "down" (car faces ↓) or "up" (car faces ↑)
 *   highlighted – true when the drivable car's sensor detects this bay
 *   disabled    – true during driving mode (prevent manual clicks)
 *   onClick     – callback when the bay is clicked
 */

import React from "react";
import CarIcon from "./CarIcon";

function ParkingSpot({ spot, direction, highlighted, disabled, onClick }) {
  const isFree = spot.status === "free";
  const isReserved = spot.reserved === true;
  const isSensorOnly = !isFree && !isReserved;

  const facingClass = direction === "up" ? "bay-facing-up" : "bay-facing-down";
  const sensorClass = highlighted ? "bay-sensor" : "";
  const statusClass = isFree ? "bay-free" : isReserved ? "bay-occupied" : "bay-sensor-occupied";

  return (
    <button
      className={`parking-bay ${statusClass} ${facingClass} ${sensorClass}`}
      data-spot-id={spot.id}
      data-status={spot.status}
      onClick={() => !disabled && onClick(spot)}
      title={
        isFree
          ? `${spot.label} — $${spot.price.toFixed(2)}/hr`
          : isReserved
          ? `Release ${spot.label}`
          : `${spot.label} — sensor detected`
      }
    >
      <span className="bay-label">{spot.label}</span>

      {isReserved ? (
        <span className="parked-car-hitbox" data-parked-hitbox="true" aria-hidden>
          <CarIcon />
        </span>
      ) : isSensorOnly ? (
        <span className="bay-detecting">OCCUPIED</span>
      ) : (
        <span className="bay-price">${spot.price.toFixed(2)}/hr</span>
      )}
    </button>
  );
}

export default ParkingSpot;
