import React from "react";

const BODY_ORDER = [
  "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
  "TrueNode", "Lilith", "Chiron",
];
const POINT_ORDER = ["Asc", "DSC", "MC", "IC", "Vertex", "Fortune"];

function formatPosition(item: any) {
  if (!item || item.available === false || !item.sign || !Number.isFinite(Number(item.deg_in_sign))) return "Unavailable";
  const value = Number(item.deg_in_sign);
  let deg = Math.floor(value);
  let minutes = Math.round((value - deg) * 60);
  if (minutes >= 60) {
    deg += 1;
    minutes = 0;
  }
  return `${item.sign} ${deg}° ${String(minutes).padStart(2, "0")}′`;
}

function row(name: string, item: any, timeUnknown: boolean) {
  const house = !timeUnknown && Number.isFinite(Number(item?.house)) ? `House ${item.house}` : "—";
  const motion = typeof item?.retrograde === "boolean" ? (item.retrograde ? "Retrograde" : "Direct") : "—";
  return (
    <tr key={name}>
      <td><strong>{name === "TrueNode" ? "True Node" : name}</strong></td>
      <td>{formatPosition(item)}</td>
      <td>{house}</td>
      <td>{motion}</td>
    </tr>
  );
}

export default function PrecisePositions({ chart }: { chart: any }) {
  if (!chart) return null;
  const planets = chart.planets || {};
  const points = chart.points || {};
  return (
    <div className="precisePositions">
      <div className="subsectionHeading">
        <h3>Precise positions</h3>
        <p className="muted">
          Tropical geocentric longitudes. Displayed to the nearest arcminute; calculations retain higher precision internally.
        </p>
      </div>
      <div className="positionTableWrap">
        <table className="positionTable">
          <thead><tr><th>Body / point</th><th>Position</th><th>House</th><th>Motion</th></tr></thead>
          <tbody>
            {BODY_ORDER.filter((name) => planets[name]).map((name) => row(name, planets[name], Boolean(chart.time_unknown)))}
            {POINT_ORDER.filter((name) => points[name]).map((name) => row(name, points[name], Boolean(chart.time_unknown)))}
          </tbody>
        </table>
      </div>
      {chart.timezone && (
        <p className="calculationMeta muted">
          Time zone: <strong>{chart.timezone}</strong>
          {Number.isFinite(Number(chart.tz_offset_hours_resolved)) ? ` · resolved UTC offset: ${Number(chart.tz_offset_hours_resolved) >= 0 ? "+" : ""}${Number(chart.tz_offset_hours_resolved)} h` : ""}
        </p>
      )}
    </div>
  );
}
