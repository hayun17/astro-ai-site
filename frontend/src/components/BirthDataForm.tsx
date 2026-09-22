import React, { useEffect, useRef, useState } from "react";
import { GeoHit, searchPlaces } from "../lib/api";

export type BirthDraft = {
  name: string;
  year: number | "";
  month: number | "";
  day: number | "";
  hour: number | "";
  minute: number | "";
  latitude: number | "";
  longitude: number | "";
  tz_offset_hours: number | "";
  house_system: string;
  birthplace: string;
  geo: GeoHit | null;
  useAdvancedCoords: boolean;
  timeUnknown: boolean;
};

export function makeBirthDraft(name = ""): BirthDraft {
  return {
    name,
    year: "",
    month: "",
    day: "",
    hour: "",
    minute: "",
    latitude: "",
    longitude: "",
    tz_offset_hours: "",
    house_system: "P",
    birthplace: "",
    geo: null,
    useAdvancedCoords: false,
    timeUnknown: false,
  };
}

type Props = {
  value: BirthDraft;
  onChange: (value: BirthDraft) => void;
  title?: string;
  compact?: boolean;
};

export default function BirthDataForm({ value, onChange, title, compact = false }: Props) {
  const [suggestions, setSuggestions] = useState<GeoHit[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const seq = useRef(0);

  const patch = (p: Partial<BirthDraft>) => onChange({ ...value, ...p });

  useEffect(() => {
    const q = value.birthplace.trim();
    if (value.useAdvancedCoords || q.length < 2 || value.geo?.displayName === q) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    const current = ++seq.current;
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const hits = await searchPlaces(q, 6);
        if (current !== seq.current) return;
        setSuggestions(hits);
        setOpen(hits.length > 0);
      } catch {
        if (current === seq.current) {
          setSuggestions([]);
          setOpen(false);
        }
      } finally {
        if (current === seq.current) setLoading(false);
      }
    }, 350);
    return () => window.clearTimeout(timer);
  }, [value.birthplace, value.geo?.displayName, value.useAdvancedCoords]);

  return (
    <div className={`birthForm ${compact ? "birthFormCompact" : ""}`}>
      {title && <h3>{title}</h3>}
      <label className="field fieldWide">
        Name
        <input value={value.name} onChange={(e) => patch({ name: e.target.value })} autoComplete="name" />
      </label>

      <div className="birthDateTimeGrid">
        <div className="field dateFieldGroup">
          <span className="fieldLabel">Date of birth <span className="dateFormatHint">DD / MM / YYYY</span></span>
          <div className="dateParts" aria-label="Date of birth, day month year">
            <label className="datePart">
              <span>Day</span>
              <input
                type="number"
                inputMode="numeric"
                min={1}
                max={31}
                value={value.day}
                onChange={(e) => patch({ day: e.target.value === "" ? "" : Number(e.target.value) })}
                aria-label="Birth day"
              />
            </label>
            <label className="datePart datePartMonth">
              <span>Month</span>
              <select value={value.month} onChange={(e) => patch({ month: e.target.value === "" ? "" : Number(e.target.value) })} aria-label="Birth month">
                <option value="" disabled>Select month</option>
                <option value={1}>01 · January</option><option value={2}>02 · February</option><option value={3}>03 · March</option>
                <option value={4}>04 · April</option><option value={5}>05 · May</option><option value={6}>06 · June</option>
                <option value={7}>07 · July</option><option value={8}>08 · August</option><option value={9}>09 · September</option>
                <option value={10}>10 · October</option><option value={11}>11 · November</option><option value={12}>12 · December</option>
              </select>
            </label>
            <label className="datePart">
              <span>Year</span>
              <input
                type="number"
                inputMode="numeric"
                min={1}
                max={9999}
                value={value.year}
                onChange={(e) => patch({ year: e.target.value === "" ? "" : Number(e.target.value) })}
                aria-label="Birth year"
              />
            </label>
          </div>
        </div>
        <label className="field">
          Time <span className="dateFormatHint">24-hour</span>
          <input
            type="time"
            disabled={value.timeUnknown}
            value={value.hour === "" || value.minute === "" ? "" : `${String(value.hour).padStart(2, "0")}:${String(value.minute).padStart(2, "0")}`}
            onChange={(e) => {
              const [hour, minute] = e.target.value.split(":").map(Number);
              if (!e.target.value) { patch({ hour: "", minute: "" }); return; }
              if (Number.isFinite(hour) && Number.isFinite(minute)) patch({ hour, minute });
            }}
          />
        </label>
        <label className="unknownTimeToggle">
          <input type="checkbox" checked={value.timeUnknown} onChange={(e) => patch({ timeUnknown: e.target.checked })} />
          <span>I don’t know my birth time</span>
        </label>
      </div>

      <div className="field birthplaceField">
        <span className="fieldLabel">Birthplace (City, Country)</span>
        <div className="placeSearchWrap">
          <input
            value={value.birthplace}
            onChange={(e) => patch({ birthplace: e.target.value, geo: null })}
            onFocus={() => suggestions.length > 0 && setOpen(true)}
            onBlur={() => window.setTimeout(() => setOpen(false), 140)}
            placeholder="Start typing: Ankara, London, New York…"
            autoComplete="off"
            autoCapitalize="words"
            spellCheck={false}
            role="combobox"
            aria-expanded={open}
          />
          {open && suggestions.length > 0 && (
            <div className="placeSuggestions" role="listbox">
              {suggestions.map((hit, idx) => (
                <button
                  type="button"
                  className="placeSuggestion"
                  key={`${hit.id ?? "x"}-${hit.lat}-${hit.lon}-${idx}`}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => {
                    patch({
                      birthplace: hit.displayName,
                      geo: hit,
                      latitude: hit.lat,
                      longitude: hit.lon,
                    });
                    setSuggestions([]);
                    setOpen(false);
                  }}
                >
                  <span className="placeSuggestionName">{hit.displayName}</span>
                  <span className="placeSuggestionMeta">{hit.timezone || `${hit.lat.toFixed(3)}, ${hit.lon.toFixed(3)}`}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <span className="help">
          {loading
            ? "Looking up coordinates…"
            : value.geo
            ? `Resolved: ${value.geo.displayName} · ${value.geo.timezone || `${value.geo.lat.toFixed(3)}, ${value.geo.lon.toFixed(3)}`}`
            : "Choose a suggestion for automatic coordinates/timezone, or use Advanced."}
        </span>
      </div>

      <div className="birthPrefsGrid">
        <label className="field">
          House system
          <select value={value.house_system} disabled={value.timeUnknown} onChange={(e) => patch({ house_system: e.target.value })}>
            <option value="P">Placidus (P)</option>
            <option value="W">Whole Sign (W)</option>
            <option value="K">Koch (K)</option>
            <option value="R">Regiomontanus (R)</option>
            <option value="C">Campanus (C)</option>
            <option value="E">Equal (E)</option>
          </select>
        </label>
        <label className="field">
          Timezone / UTC offset
          {value.geo?.timezone && !value.useAdvancedCoords ? (
            <input value={`Automatic · ${value.geo.timezone}`} readOnly />
          ) : (
            <input
              type="number"
              inputMode="decimal"
              step="0.25"
              min={-14}
              max={14}
              value={value.tz_offset_hours}
              onChange={(e) => patch({ tz_offset_hours: e.target.value === "" ? "" : Number(e.target.value) })}
            />
          )}
        </label>
      </div>

      <details className="advanced">
        <summary>Advanced <span className="muted">(manual coordinates)</span></summary>
        <div className="manualGrid">
          <label className="unknownTimeToggle">
            <input type="checkbox" checked={value.useAdvancedCoords} onChange={(e) => patch({ useAdvancedCoords: e.target.checked })} />
            <span>Use manual latitude/longitude</span>
          </label>
          <label className="field">
            Latitude
            <input type="number" step="0.0001" min={-90} max={90} disabled={!value.useAdvancedCoords} value={value.latitude} onChange={(e) => patch({ latitude: e.target.value === "" ? "" : Number(e.target.value) })} />
          </label>
          <label className="field">
            Longitude
            <input type="number" step="0.0001" min={-180} max={180} disabled={!value.useAdvancedCoords} value={value.longitude} onChange={(e) => patch({ longitude: e.target.value === "" ? "" : Number(e.target.value) })} />
          </label>
        </div>
      </details>

      {value.timeUnknown && (
        <p className="birthHint">Unknown-time mode will not guess houses, angles or time-sensitive Moon aspects.</p>
      )}
      <span className="geoAttribution">Location search: Open-Meteo · GeoNames data</span>
    </div>
  );
}
