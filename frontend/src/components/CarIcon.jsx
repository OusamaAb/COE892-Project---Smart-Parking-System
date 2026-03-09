/**
 * CarIcon.jsx — Shared top-down car SVG with a configurable body color.
 *
 * Props:
 *   color      – primary body color (default: "#3b82f6" blue)
 *   darkColor  – darker shade for roof/mirrors (default: derived from color)
 *   className  – optional extra CSS class
 */

import React from "react";

const PRESETS = {
  "#3b82f6": { dark: "#2563eb", glass: "#93c5fd" },
  "#ef4444": { dark: "#dc2626", glass: "#fca5a5" },
  "#22c55e": { dark: "#16a34a", glass: "#86efac" },
};

function CarIcon({ color = "#3b82f6", className = "" }) {
  const preset = PRESETS[color] || {
    dark: color,
    glass: "#93c5fd",
  };

  return (
    <svg
      className={`car-svg ${className}`}
      viewBox="0 0 50 90"
      xmlns="http://www.w3.org/2000/svg"
    >
      <ellipse cx="25" cy="48" rx="22" ry="40" fill="#00000030" />
      <rect x="7" y="8" width="36" height="74" rx="12" ry="12" fill={color} />
      <rect x="11" y="24" width="28" height="36" rx="6" fill={preset.dark} />
      <rect x="13" y="26" width="24" height="14" rx="4" fill={preset.glass} opacity="0.8" />
      <rect x="13" y="50" width="24" height="10" rx="4" fill={preset.glass} opacity="0.6" />
      <rect x="12" y="9" width="8" height="4" rx="2" fill="#fde68a" />
      <rect x="30" y="9" width="8" height="4" rx="2" fill="#fde68a" />
      <rect x="12" y="77" width="8" height="4" rx="2" fill="#ef4444" />
      <rect x="30" y="77" width="8" height="4" rx="2" fill="#ef4444" />
      <ellipse cx="5"  cy="30" rx="3" ry="2" fill={preset.dark} />
      <ellipse cx="45" cy="30" rx="3" ry="2" fill={preset.dark} />
      <rect x="3"  y="18" width="6" height="12" rx="3" fill="#1e293b" />
      <rect x="41" y="18" width="6" height="12" rx="3" fill="#1e293b" />
      <rect x="3"  y="60" width="6" height="12" rx="3" fill="#1e293b" />
      <rect x="41" y="60" width="6" height="12" rx="3" fill="#1e293b" />
    </svg>
  );
}

export default CarIcon;
