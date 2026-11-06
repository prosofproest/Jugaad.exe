"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge, Field, Icon, PageHeader } from "@/components/workspace/ui";

const FAQS = [
  {
    q: "Is the photo assessment a diagnosis?",
    a: "No. It is an assistive visual comparison with known symptoms. It can abstain, show a confidence band instead of a percentage, and never replaces a field inspection, laboratory test or expert diagnosis.",
  },
  {
    q: "What does the confidence band mean?",
    a: "High, medium and low are bands derived from the decision function. Until calibration is approved, the app does not show a numeric probability. A band is not a guarantee.",
  },
  {
    q: "Why can the area outlook say low risk when disease is present?",
    a: "An area outlook describes the likelihood of a threat in a defined area and time window from available data. Low risk does not mean the disease is absent. Coverage and freshness are shown next to every outlook.",
  },
  {
    q: "Can the assistant tell me which chemical to spray?",
    a: "No. The assistant never gives product names, doses, mixtures or intervals. Contact your extension officer or an approved local advisory for treatment decisions.",
  },
  {
    q: "What happens when I am offline?",
    a: "Photos, videos, notes and GPS are saved in a local queue. They sync when a connection returns. Nothing is discarded, and queued captures are labelled.",
  },
  {
    q: "Can I correct an AI result?",
    a: "A farmer can request expert review. An expert or field agent can verify, correct or reject the AI match. The original prediction is preserved and the review is appended to the audit trail.",
  },
];

export default function HelpPage() {
  const [sent, setSent] = useState(false);
  const [topic, setTopic] = useState("Using the app");

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Help & support"
        title="How can we help?"
        lede="Guidance for using CropSentinel, understanding uncertainty, working offline and reaching a human when it matters."
        actions={<Link href="/assistant" className="ws-button ws-button-primary"><Icon name="assistant" size={16} /> Ask the assistant</Link>}
      />

      <div className="ws-help-grid">
        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Start here</p><h2>Quick guide</h2></div></div>
          <div className="ws-help-steps">
            {[
              { icon: "farm" as const, title: "Register your farm", body: "Add name, village, GPS location, area, plots and crop groups." },
              { icon: "scan" as const, title: "Capture what you see", body: "Photograph the affected plant part, add notes and save GPS with permission." },
              { icon: "analysis" as const, title: "Read the assessment", body: "Check symptoms, severity, confidence band, alternatives and the next safe step." },
              { icon: "expert" as const, title: "Ask a human", body: "Request expert verification for uncertain, severe or fast-spreading cases." },
              { icon: "monitoring" as const, title: "Follow up", body: "Compare the same plant after 5–7 days and record treatment effectiveness." },
            ].map((step) => (
              <div key={step.title} className="ws-help-step">
                <span className="ws-role-icon"><Icon name={step.icon} size={18} /></span>
                <div><strong>{step.title}</strong><p className="ws-small ws-muted">{step.body}</p></div>
              </div>
            ))}
          </div>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">FAQ</p><h2>Common questions</h2></div><Badge tone="info">Safety first</Badge></div>
          <div className="ws-faq">
            {FAQS.map((faq) => (
              <details key={faq.q}>
                <summary>{faq.q}<Icon name="plus" size={16} /></summary>
                <p>{faq.a}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Contact</p><h2>Reach a human</h2></div></div>
          <div className="ws-contact-list">
            <div><Icon name="user" size={17} /><div><strong>District plant health clinic</strong><span className="ws-small ws-muted">Mon–Sat, 09:00–17:00 · Krishnagiri District</span></div><Badge tone="ok">Available</Badge></div>
            <div><Icon name="location" size={17} /><div><strong>Block extension office</strong><span className="ws-small ws-muted">Walk-in support and field visits</span></div><Badge tone="ok">Available</Badge></div>
            <div><Icon name="assistant" size={17} /><div><strong>Kisan call centre</strong><span className="ws-small ws-muted">Local-language advice · 24×7</span></div><Badge tone="neutral">Phone</Badge></div>
          </div>
          <form
            className="ws-form ws-mt"
            onSubmit={(event) => {
              event.preventDefault();
              setSent(true);
            }}
          >
            <Field label="Support topic">
              <select value={topic} onChange={(event) => setTopic(event.target.value)}>
                <option>Using the app</option>
                <option>Understanding a photo assessment</option>
                <option>Expert verification</option>
                <option>Offline sync</option>
                <option>Privacy or data request</option>
              </select>
            </Field>
            <Field label="Message">
              <textarea rows={3} placeholder="Describe what you need help with. Do not include personal or sensitive data." required />
            </Field>
            <div className="ws-form-actions">
              {sent ? <span className="ws-saved"><Icon name="check" size={15} /> Request saved in this demo</span> : <span className="ws-small ws-muted">We reply in your selected language where possible.</span>}
              <button type="submit" className="ws-button ws-button-primary">Send request</button>
            </div>
          </form>
        </section>

        <section className="ws-panel">
          <div className="ws-panel-head"><div><p className="ws-eyebrow">Reference</p><h2>What the words mean</h2></div></div>
          <dl className="ws-glossary">
            <div><dt>Photo assessment</dt><dd>Assistive comparison of one photo with known symptom patterns.</dd></div>
            <div><dt>Area outlook</dt><dd>Time-bound regional risk for a crop and pest or disease. Never a confirmed outbreak.</dd></div>
            <div><dt>Confidence band</dt><dd>High, medium or low evidence band. Not a validated percentage.</dd></div>
            <div><dt>Coverage</dt><dd>How much verified reporting supports an area result.</dd></div>
            <div><dt>Verification</dt><dd>A human review that confirms, corrects or rejects an automated match.</dd></div>
            <div><dt>Abstention</dt><dd>“No assessment yet” — the honest outcome when evidence is insufficient.</dd></div>
          </dl>
        </section>
      </div>

      <div className="ws-banner ws-banner-info">
        <Icon name="shield" size={18} />
        <div>
          <strong>Safety boundary</strong>
          <p>This app supports decisions; it does not replace field inspection. It never confirms a diagnosis, never declares an outbreak and never recommends a pesticide dose.</p>
        </div>
      </div>
    </div>
  );
}
