/**
 * parkingApi.js — Axios helpers for the Smart Parking System gateway.
 *
 * The frontend talks ONLY to the gateway (port 8000).  The gateway
 * fans out to the internal microservices.
 */

import axios from "axios";

const BASE_URL = "http://localhost:8000";

/* ---------- Spots (enriched with price by the gateway) ---------- */

/**
 * @param {number} extraOccupied 0 = rate from actual occupancy only;
 *   1 = assume one more car for surge (preview before you take a spot).
 */
export async function fetchSpots(extraOccupied = 1) {
  const response = await axios.get(`${BASE_URL}/spots`, {
    params: { extra_occupied: extraOccupied },
  });
  return response.data;
}

/* ---------- Sensor events ---------- */

export async function sendSensorEvent(spotId, eventType) {
  const response = await axios.post(`${BASE_URL}/sensor-event`, {
    spot_id: spotId,
    event_type: eventType,
  });
  return response.data;
}

/* ---------- Reservations ---------- */

export async function createReservation(spotId, hours) {
  const response = await axios.post(`${BASE_URL}/reservations`, {
    spot_id: spotId,
    hours,
  });
  return response.data;
}

export async function releaseReservation(reservationId) {
  const response = await axios.delete(
    `${BASE_URL}/reservations/${reservationId}`
  );
  return response.data;
}

export async function checkSpotReservation(spotId) {
  const response = await axios.get(
    `${BASE_URL}/reservations/spot/${spotId}`
  );
  return response.data;
}

export async function listReservations() {
  const response = await axios.get(`${BASE_URL}/reservations`);
  return response.data;
}

/* ---------- Pricing ---------- */

export async function fetchRate() {
  const response = await axios.get(`${BASE_URL}/pricing/rate`);
  return response.data;
}

/* ---------- Lot clock (simulated session time) ---------- */

export async function fetchLotClock() {
  const response = await axios.get(`${BASE_URL}/lot-clock`);
  return response.data;
}

/* ---------- Health ---------- */

export async function healthCheck() {
  const response = await axios.get(`${BASE_URL}/health`);
  return response.data;
}
