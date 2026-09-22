import React from "react";

type Props = { percent: number; label: string };

export default function CalculationProgress({ percent, label }: Props) {
  const safe = Math.max(0, Math.min(100, Math.round(percent)));
  return (
    <div className="calcProgress" role="status" aria-live="polite" aria-label={`Calculation progress ${safe}%`}>
      <div className="calcProgressTop"><span>{label}</span><strong>{safe}%</strong></div>
      <div className="calcProgressTrack"><div className="calcProgressFill" style={{ width: `${safe}%` }} /></div>
      <div className="calcProgressStars" aria-hidden="true">✦ · ✧ · ✦</div>
    </div>
  );
}
