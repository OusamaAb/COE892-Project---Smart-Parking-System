/**
 * DrivableCar.jsx — A keyboard-controlled car that drives over the lot.
 *
 * Key change from v1: collision detection now checks ALL bays, not just
 * free ones.  This is critical because the sensor_service marks a spot
 * occupied the moment the car enters — if we only checked free bays,
 * the car would "lose" its overlap as soon as the backend updates.
 *
 * Props:
 *   lotRef              – ref to .lot-surface
 *   paused              – if true, keyboard input is ignored (modal open)
 *   onSensorChange(id)  – called when the car enters/leaves any bay
 *   onPark(spotId)      – called when Space is pressed while in a bay
 *   onCancel()          – called on Escape
 */

import React, { useEffect, useRef } from "react";
import CarIcon from "./CarIcon";

const CAR_W = 36;
const CAR_H = 54;
const SPEED = 3;

function DrivableCar({ lotRef, paused, onSensorChange, onPark, onCancel }) {
  const carRef = useRef(null);
  const posRef = useRef({ x: 0, y: 0 });
  const rotRef = useRef(180);
  const keysRef = useRef(new Set());
  const hoveredRef = useRef(null);
  const pausedRef = useRef(paused);

  const onSensorRef = useRef(onSensorChange);
  const onParkRef = useRef(onPark);
  const onCancelRef = useRef(onCancel);
  useEffect(() => { onSensorRef.current = onSensorChange; }, [onSensorChange]);
  useEffect(() => { onParkRef.current = onPark; },           [onPark]);
  useEffect(() => { onCancelRef.current = onCancel; },       [onCancel]);
  useEffect(() => { pausedRef.current = paused; },           [paused]);

  useEffect(() => {
    if (lotRef.current) {
      const lotW = lotRef.current.offsetWidth;
      posRef.current = { x: (lotW / 2) - (CAR_W / 2), y: 28 };
    }

    function onKeyDown(e) {
      if (pausedRef.current) return;
      const key = e.key;
      if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight",
           "w","a","s","d"," ","Escape"].includes(key)) {
        e.preventDefault();
      }
      if (key === " " && hoveredRef.current !== null) {
        onParkRef.current(hoveredRef.current);
        return;
      }
      if (key === "Escape") { onCancelRef.current(); return; }
      keysRef.current.add(key);
    }

    function onKeyUp(e) { keysRef.current.delete(e.key); }

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);

    let animId;

    function tick() {
      if (!lotRef.current || !carRef.current) {
        animId = requestAnimationFrame(tick);
        return;
      }

      if (!pausedRef.current) {
        const keys = keysRef.current;
        let { x, y } = posRef.current;
        let rot = rotRef.current;
        let moved = false;

        if (keys.has("ArrowUp")    || keys.has("w")) { y -= SPEED; rot = 0;   moved = true; }
        if (keys.has("ArrowDown")  || keys.has("s")) { y += SPEED; rot = 180; moved = true; }
        if (keys.has("ArrowLeft")  || keys.has("a")) { x -= SPEED; rot = 270; moved = true; }
        if (keys.has("ArrowRight") || keys.has("d")) { x += SPEED; rot = 90;  moved = true; }

        const lotW = lotRef.current.offsetWidth;
        const lotH = lotRef.current.offsetHeight;
        x = Math.max(0, Math.min(lotW - CAR_W, x));
        y = Math.max(0, Math.min(lotH - CAR_H, y));

        posRef.current = { x, y };
        rotRef.current = rot;

        carRef.current.style.transform =
          `translate(${x}px, ${y}px) rotate(${rot}deg)`;

        if (moved) checkOverlap(x, y);
      }

      animId = requestAnimationFrame(tick);
    }

    animId = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      cancelAnimationFrame(animId);
    };
  }, [lotRef]);

  /**
   * Check overlap against ALL bays — not just free ones.
   * The ParkingLot component handles the business logic of what to do.
   */
  function checkOverlap(carX, carY) {
    const lot = lotRef.current;
    if (!lot) return;

    const lotRect = lot.getBoundingClientRect();
    const bays = lot.querySelectorAll("[data-spot-id]");
    let foundId = null;

    bays.forEach((bay) => {
      const r = bay.getBoundingClientRect();
      const bx = r.left - lotRect.left;
      const by = r.top  - lotRect.top;

      const overlapX = Math.max(0, Math.min(carX + CAR_W, bx + r.width)  - Math.max(carX, bx));
      const overlapY = Math.max(0, Math.min(carY + CAR_H, by + r.height) - Math.max(carY, by));
      const overlapArea = overlapX * overlapY;

      if (overlapArea > (CAR_W * CAR_H) * 0.4) {
        foundId = parseInt(bay.dataset.spotId, 10);
      }
    });

    if (foundId !== hoveredRef.current) {
      hoveredRef.current = foundId;
      onSensorRef.current(foundId);
    }
  }

  return (
    <div
      ref={carRef}
      className="drivable-car"
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: CAR_W,
        height: CAR_H,
        transform: `translate(${posRef.current.x}px, ${posRef.current.y}px) rotate(${rotRef.current}deg)`,
      }}
    >
      <CarIcon color="#ef4444" className="drivable-car-svg" />
    </div>
  );
}

export default DrivableCar;
