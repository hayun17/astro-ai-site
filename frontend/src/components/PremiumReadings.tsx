import React from "react";

type ReadingCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  features: string[];
  price?: string;
  checkoutUrl?: string;
  featured?: boolean;
};

function safeCheckoutUrl(raw?: string) {
  const value = (raw || "").trim();
  if (!value) return "";
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.toString() : "";
  } catch {
    return "";
  }
}

function ReadingCard({ eyebrow, title, description, features, price, checkoutUrl, featured }: ReadingCardProps) {
  const url = safeCheckoutUrl(checkoutUrl);
  return (
    <article className={`premiumCard${featured ? " featured" : ""}`}>
      <div className="premiumEyebrow">{eyebrow}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {price && <div className="premiumPrice">{price}</div>}
      <ul>
        {features.map((feature) => <li key={feature}>{feature}</li>)}
      </ul>
      {url ? (
        <a className="premiumCta" href={url} target="_blank" rel="noopener noreferrer">Choose this reading</a>
      ) : (
        <button className="premiumCta disabled" type="button" disabled>Checkout coming soon</button>
      )}
    </article>
  );
}

export default function PremiumReadings() {
  const paidPrice = (import.meta.env.VITE_PAID_READING_PRICE as string) || "";
  const deepPrice = (import.meta.env.VITE_DEEP_READING_PRICE as string) || "";
  const paidUrl = (import.meta.env.VITE_PAID_READING_URL as string) || "";
  const deepUrl = (import.meta.env.VITE_DEEP_READING_URL as string) || "";

  return (
    <section className="card premiumSection" id="premium-readings">
      <div className="premiumIntro">
        <span className="premiumKicker">A little more personal ✨</span>
        <h2>Premium Readings</h2>
        <p>
          The free tools show you the chart. Premium readings turn the whole chart into one carefully written story — delivered as a polished PDF you can keep, highlight and come back to.
        </p>
      </div>

      <div className="premiumReportPromise" aria-label="Premium report format">
        <div><strong>Your natal chart comes first.</strong><span>The opening page includes the full birth-chart wheel so every interpretation has a visible map behind it.</span></div>
        <div><strong>Written like a real reading.</strong><span>Long-form synthesis, gentle transitions and specific chart patterns — not copied placement blurbs stitched together.</span></div>
        <div><strong>Made to keep.</strong><span>Soft editorial typography, clear chapters, chart tables and a warm closing note in a downloadable PDF.</span></div>
      </div>

      <div className="premiumGrid">
        <ReadingCard
          eyebrow="Paid Reading"
          title="Personalized Reading"
          description="A thoughtful whole-chart reading for someone who wants more than individual placements. The report connects the themes that repeat across your chart and explains how they can show up together."
          price={paidPrice}
          checkoutUrl={paidUrl}
          features={[
            "Beautifully designed long-form PDF",
            "Full natal chart wheel on the opening page",
            "Big Three, mind, love, drive, home and career synthesis",
            "Strongest aspects and repeating chart themes woven together",
            "Practical reflection points and a personal closing note",
          ]}
        />
        <ReadingCard
          eyebrow="Deep, Personal Reading"
          title="Deep Personal Reading"
          description="For the person who wants the contradictions, repeating patterns and personal questions explored with more room. This is the slower, more intimate version of the reading."
          price={deepPrice}
          checkoutUrl={deepUrl}
          featured
          features={[
            "Everything in the Personalized Reading",
            "A longer, more layered whole-chart synthesis",
            "Up to 3 personal questions or themes addressed directly",
            "Deeper relationship, boundaries and inner-pattern analysis",
            "Contradictory chart signatures explored instead of flattened",
            "Premium keepsake PDF with the natal chart at the front",
          ]}
        />
      </div>
      <p className="premiumFinePrint muted">
        Astrology readings are interpretive and intended for reflection/entertainment. They are not medical, legal, financial or mental-health advice.
      </p>
    </section>
  );
}
