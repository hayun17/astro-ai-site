import React from "react";

function inline(text: string, keyPrefix: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={`${keyPrefix}-b-${i}`}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={`${keyPrefix}-t-${i}`}>{part}</React.Fragment>;
  });
}

export default function InterpretationView({ text }: { text?: string }) {
  const lines = String(text || "").replace(/\r/g, "").split("\n");
  const out: React.ReactNode[] = [];
  let bullets: string[] = [];

  const flushBullets = () => {
    if (!bullets.length) return;
    const start = out.length;
    out.push(
      <ul className="readingList" key={`ul-${start}`}>
        {bullets.map((item, i) => <li key={`li-${start}-${i}`}>{inline(item, `li-${start}-${i}`)}</li>)}
      </ul>
    );
    bullets = [];
  };

  lines.forEach((raw, idx) => {
    const line = raw.trim();
    if (!line) { flushBullets(); return; }
    if (line.startsWith("- ")) { bullets.push(line.slice(2)); return; }
    flushBullets();
    if (line.startsWith("### ")) out.push(<h3 className="readingHeading" key={`h3-${idx}`}>{inline(line.slice(4), `h3-${idx}`)}</h3>);
    else if (line.startsWith("## ")) out.push(<h2 className="readingHeading readingHeading2" key={`h2-${idx}`}>{inline(line.slice(3), `h2-${idx}`)}</h2>);
    else if (line.startsWith("# ")) out.push(<h2 className="readingHeading readingHeading2" key={`h1-${idx}`}>{inline(line.slice(2), `h1-${idx}`)}</h2>);
    else out.push(<p className="readingParagraph" key={`p-${idx}`}>{inline(line, `p-${idx}`)}</p>);
  });
  flushBullets();

  return <div className="readingOutput">{out.length ? out : <p className="muted">No interpretation available.</p>}</div>;
}
