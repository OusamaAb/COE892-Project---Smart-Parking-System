/**
 * parkingApi.js — Axios helpers for the Smart Parking System gateway.
 *
 * The frontend talks ONLY to the gateway (port 8000).  The gateway
 * fans out to the internal microservices.
 */

import axios from "axios";

const BASE_URL = "http://localhost:8000";

/* ---------- Spots (enriched with price by the gateway) ---------- */

export async function fetchSpots() {
  const response = await axios.get(`${BASE_URL}/spots`);
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

/* ---------- Health ---------- */

export async function healthCheck() {
  const response = await axios.get(`${BASE_URL}/health`);
  return response.data;
}
