import React, { useEffect, useMemo, useState } from "react";

type Product = "personalized_reading" | "deep_reading";

type Buyer = {
  full_name: string;
  email: string;
  phone: string;
  identity_number: string;
  address: string;
  city: string;
  country: string;
};

type Props = {
  onCheckout: (product: Product, buyer: Buyer, questions: string[]) => Promise<void>;
  checkoutBusy?: boolean;
  checkoutError?: string | null;
  apiBase: string;
};

type ReadingCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  features: string[];
  price?: string;
  featured?: boolean;
  onChoose: () => void;
  enabled: boolean;
};

function ReadingCard({ eyebrow, title, description, features, price, featured, onChoose, enabled }: ReadingCardProps) {
  return (
    <article className={`premiumCard${featured ? " featured" : ""}`}>
      <div className="premiumEyebrow">{eyebrow}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {price && <div className="premiumPrice">{price}</div>}
      <ul>{features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
      <button className="premiumCta" type="button" onClick={onChoose} disabled={!enabled}>
        {enabled ? "Choose this reading" : "Checkout coming soon"}
      </button>
    </article>
  );
}

export default function PremiumReadings({ onCheckout, checkoutBusy = false, checkoutError, apiBase }: Props) {
  const [product, setProduct] = useState<Product | null>(null);
  const [buyer, setBuyer] = useState<Buyer>({ full_name:"", email:"", phone:"", identity_number:"", address:"", city:"", country:"Turkey" });
  const [questions, setQuestions] = useState(["", "", ""]);
  const [catalog, setCatalog] = useState<any>({ready:false,products:{}});

  useEffect(() => {
    let alive = true;
    fetch(`${apiBase}/api/payments/config`).then(r=>r.ok?r.json():null).then(data=>{ if(alive && data) setCatalog(data); }).catch(()=>{});
    return () => { alive = false; };
  }, [apiBase]);

  const paid = catalog?.products?.personalized_reading;
  const deep = catalog?.products?.deep_reading;
  const enabled = Boolean(catalog?.ready);
  const selectedTitle = product === "deep_reading" ? "Deep Personal Reading" : "Personalized Reading";
  const selectedPrice = product === "deep_reading" ? deep?.price : paid?.price;
  const priceText = (p:any) => p?.price ? `₺${p.price}` : "";
  const cleanQuestions = useMemo(() => questions.map(x=>x.trim()).filter(Boolean), [questions]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!product) return;
    await onCheckout(product, buyer, product === "deep_reading" ? cleanQuestions : []);
  }

  return (
    <section className="card premiumSection" id="premium-readings">
      <div className="premiumIntro">
        <span className="premiumKicker">A little more personal ✨</span>
        <h2>Premium Readings</h2>
        <p>The free tools show you the chart. Premium readings turn the whole chart into one carefully written story — delivered as a polished PDF you can keep, highlight and come back to.</p>
      </div>

      <div className="premiumReportPromise" aria-label="Premium report format">
        <div><strong>Your natal chart comes first.</strong><span>The opening page includes the full birth-chart wheel so every interpretation has a visible map behind it.</span></div>
        <div><strong>Written like a real reading.</strong><span>Long-form synthesis, gentle transitions and specific chart patterns — not copied placement blurbs stitched together.</span></div>
        <div><strong>Secure checkout.</strong><span>Your payment is completed on a secure hosted payment page. AstroMYLA receives only the verified payment result before unlocking your report.</span></div>
      </div>

      <div className="premiumGrid">
        <ReadingCard eyebrow="Paid Reading" title="Personalized Reading"
          description="A thoughtful whole-chart reading for someone who wants more than individual placements. The report connects the themes that repeat across your chart and explains how they can show up together."
          price={priceText(paid)} enabled={enabled} onChoose={()=>setProduct("personalized_reading")}
          features={["Beautifully designed long-form PDF","Full natal chart wheel on the opening page","Big Three, mind, love, drive, home and career synthesis","Strongest aspects and repeating chart themes woven together","Practical reflection points and a personal closing note"]}/>
        <ReadingCard eyebrow="Deep, Personal Reading" title="Deep Personal Reading"
          description="For the person who wants the contradictions, repeating patterns and personal questions explored with more room. This is the slower, more intimate version of the reading."
          price={priceText(deep)} enabled={enabled} featured onChoose={()=>setProduct("deep_reading")}
          features={["Everything in the Personalized Reading","A longer, more layered whole-chart synthesis","Up to 3 personal questions or themes addressed directly","Deeper relationship, boundaries and inner-pattern analysis","Contradictory chart signatures explored instead of flattened","Premium keepsake PDF with the natal chart at the front"]}/>
      </div>

      {!enabled && <p className="premiumFinePrint muted">Premium checkout is temporarily unavailable.</p>}
      <p className="premiumFinePrint muted">Astrology readings are interpretive and intended for reflection/entertainment. They are not medical, legal, financial or mental-health advice.</p>

      {product && (
        <div className="checkoutOverlay" role="dialog" aria-modal="true" aria-label="Secure reading checkout">
          <form className="checkoutModal" onSubmit={submit}>
            <button type="button" className="checkoutClose" onClick={()=>setProduct(null)} aria-label="Close checkout">×</button>
            <span className="premiumKicker">Secure checkout</span>
            <h3>{selectedTitle}</h3>
            {selectedPrice && <div className="premiumPrice">₺{selectedPrice}</div>}
            <p className="muted">You’ll continue to a secure hosted payment page. AstroMYLA does not collect or store your card details.</p>
            <div className="checkoutGrid">
              <label>Full name<input required value={buyer.full_name} onChange={e=>setBuyer({...buyer,full_name:e.target.value})}/></label>
              <label>Email<input required type="email" value={buyer.email} onChange={e=>setBuyer({...buyer,email:e.target.value})}/></label>
              <label>Phone<input required inputMode="tel" value={buyer.phone} onChange={e=>setBuyer({...buyer,phone:e.target.value})}/></label>
              <label>Identity number<input required inputMode="numeric" value={buyer.identity_number} onChange={e=>setBuyer({...buyer,identity_number:e.target.value})}/></label>
              <label className="checkoutWide">Billing address<input required value={buyer.address} onChange={e=>setBuyer({...buyer,address:e.target.value})}/></label>
              <label>City<input required value={buyer.city} onChange={e=>setBuyer({...buyer,city:e.target.value})}/></label>
              <label>Country<input required value={buyer.country} onChange={e=>setBuyer({...buyer,country:e.target.value})}/></label>
            </div>
            {product === "deep_reading" && <div className="questionFields"><strong>Optional personal questions</strong>{questions.map((q,i)=><textarea key={i} maxLength={500} placeholder={`Question ${i+1}`} value={q} onChange={e=>setQuestions(questions.map((x,j)=>j===i?e.target.value:x))}/>)}</div>}
            {checkoutError && <p className="error">{checkoutError}</p>}
            <button className="premiumCta checkoutSubmit" disabled={checkoutBusy}>{checkoutBusy ? "Opening secure checkout…" : "Continue to secure checkout"}</button>
          </form>
        </div>
      )}
    </section>
  );
}
