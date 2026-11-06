"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Icon } from "@/components/workspace/ui";
import { useWorkspace } from "@/lib/workspace/store";
import type { Language } from "@/lib/workspace/types";

export default function RegisterPage() {
  const router = useRouter();
  const { addFarm, signIn, updateProfile, setLanguage } = useWorkspace();
  const [step, setStep] = useState<1 | 2>(1);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [village, setVillage] = useState("");
  const [district, setDistrict] = useState("Krishnagiri");
  const [language, setLocalLanguage] = useState<Language>("en");
  const [farmName, setFarmName] = useState("");
  const [area, setArea] = useState("2");
  const [crop, setCrop] = useState("Tomato");
  const [variety, setVariety] = useState("Arka Rakshak");
  const [gps, setGps] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsMessage, setGpsMessage] = useState("");
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);

  function next(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim() || phone.replace(/\D/g, "").length < 10) {
      setError("Add your name and a 10-digit mobile number.");
      return;
    }
    setError("");
    setStep(2);
    if (!farmName) setFarmName(`${name.split(" ")[0] ?? "My"} Farm`);
  }

  function requestLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGps({ lat: 12.7409, lng: 77.8253 });
      setGpsMessage("Geolocation is not available. Demo coordinates added.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGps({ lat: Number(position.coords.latitude.toFixed(5)), lng: Number(position.coords.longitude.toFixed(5)) });
        setGpsMessage("GPS coordinates captured with permission.");
      },
      () => {
        setGps({ lat: 12.7409, lng: 77.8253 });
        setGpsMessage("Permission denied. You can type coordinates or use the demo location.");
      },
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!farmName.trim()) {
      setError("Give your farm a name.");
      return;
    }
    if (!consent) {
      setError("Please confirm the data consent statement.");
      return;
    }
    signIn("farmer");
    updateProfile({
      name: name.trim(),
      phone,
      email: email || `${name.toLowerCase().replace(/\s+/g, ".")}@example.in`,
      village: village || "Hosur",
      district,
    });
    setLanguage(language);
    addFarm({
      name: farmName.trim(),
      village: village || "Hosur",
      district,
      areaAcres: Number(area) || 1,
      crop,
      variety,
      lat: gps?.lat ?? 12.7409,
      lng: gps?.lng ?? 77.8253,
      soil: "Red loam",
      irrigation: "Drip",
    });
    router.push("/farms");
  }

  return (
    <div className="ws-auth ws-auth-register">
      <div className="ws-auth-visual">
        <Link href="/login" className="ws-auth-brand">
          <span className="ws-brand-mark"><Icon name="leaf" size={22} /></span>
          <span><strong>CropSentinel</strong><small>Pest & disease network</small></span>
        </Link>
        <div>
          <p className="ws-eyebrow">Farmer registration</p>
          <h1>Bring your whole farm into one clear record.</h1>
          <p>
            Register your farm, add plots and plants, and start with photo observations. You can
            add experts and field agents to your case later.
          </p>
        </div>
        <div className="ws-auth-steps">
          <div className={step >= 1 ? "ws-auth-step ws-auth-step-active" : "ws-auth-step"}>
            <span>1</span>
            <div><strong>Your account</strong><small>Name, mobile and language</small></div>
          </div>
          <div className={step >= 2 ? "ws-auth-step ws-auth-step-active" : "ws-auth-step"}>
            <span>2</span>
            <div><strong>Your farm</strong><small>Location, area and first crop</small></div>
          </div>
        </div>
        <p className="ws-auth-disclaimer">
          GPS is optional and only captured after your permission. Helper text follows the
          project&apos;s safety wording: no diagnosis, no pesticide dose recommendations.
        </p>
      </div>

      <div className="ws-auth-panel">
        <div className="ws-auth-card">
          <div className="ws-auth-head">
            <p className="ws-eyebrow">Step {step} of 2</p>
            <h2>{step === 1 ? "Create your farmer account" : "Tell us about your farm"}</h2>
          </div>

          {step === 1 ? (
            <form onSubmit={next} className="ws-form">
              <label className="ws-field">
                <span>Full name</span>
                <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ravi Kumar" />
              </label>
              <div className="ws-form-grid">
                <label className="ws-field">
                  <span>Mobile number</span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(event) => setPhone(event.target.value)}
                    placeholder="98420 11223"
                  />
                </label>
                <label className="ws-field">
                  <span>Email (optional)</span>
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.in"
                  />
                </label>
              </div>
              <div className="ws-form-grid">
                <label className="ws-field">
                  <span>Village</span>
                  <input value={village} onChange={(event) => setVillage(event.target.value)} placeholder="Hosur" />
                </label>
                <label className="ws-field">
                  <span>District</span>
                  <select value={district} onChange={(event) => setDistrict(event.target.value)}>
                    <option>Krishnagiri</option>
                    <option>Dharmapuri</option>
                    <option>Salem</option>
                  </select>
                </label>
              </div>
              <label className="ws-field">
                <span>Preferred language</span>
                <select value={language} onChange={(event) => setLocalLanguage(event.target.value as Language)}>
                  <option value="en">English</option>
                  <option value="hi">हिन्दी (Hindi)</option>
                  <option value="kn">ಕನ್ನಡ (Kannada)</option>
                </select>
              </label>
              {error ? <p className="ws-form-error" role="alert">{error}</p> : null}
              <button type="submit" className="ws-button ws-button-primary ws-button-block ws-button-large">
                Continue to farm details <Icon name="arrow" size={17} />
              </button>
              <p className="ws-auth-switch">
                Already registered? <Link href="/login">Sign in</Link>
              </p>
            </form>
          ) : (
            <form onSubmit={submit} className="ws-form">
              <label className="ws-field">
                <span>Farm name</span>
                <input value={farmName} onChange={(event) => setFarmName(event.target.value)} placeholder="Sunrise Farm" />
              </label>
              <div className="ws-form-grid">
                <label className="ws-field">
                  <span>Area (acres)</span>
                  <input
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={area}
                    onChange={(event) => setArea(event.target.value)}
                  />
                </label>
                <label className="ws-field">
                  <span>Main crop</span>
                  <select value={crop} onChange={(event) => setCrop(event.target.value)}>
                    <option>Tomato</option>
                    <option>Chilli</option>
                    <option>Brinjal</option>
                    <option>Mango</option>
                    <option>Maize</option>
                    <option>Cowpea</option>
                    <option>Beans</option>
                  </select>
                </label>
              </div>
              <label className="ws-field">
                <span>Variety</span>
                <input value={variety} onChange={(event) => setVariety(event.target.value)} />
              </label>
              <div className="ws-gps-box">
                <div>
                  <strong>Farm location</strong>
                  <p className="ws-small ws-muted">
                    {gps ? `${gps.lat.toFixed(5)}, ${gps.lng.toFixed(5)}` : "No coordinates captured yet."}
                  </p>
                  {gpsMessage ? <p className="ws-small">{gpsMessage}</p> : null}
                </div>
                <button type="button" className="ws-button ws-button-secondary" onClick={requestLocation}>
                  <Icon name="location" size={16} /> Use my GPS
                </button>
              </div>
              <label className="ws-check ws-check-top">
                <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
                I agree that my farm records and photos may be used to provide this service and
                expert verification. Photos are stored on this demo device only.
              </label>
              {error ? <p className="ws-form-error" role="alert">{error}</p> : null}
              <div className="ws-form-actions">
                <button type="button" className="ws-button ws-button-ghost" onClick={() => setStep(1)}>
                  Back
                </button>
                <button type="submit" className="ws-button ws-button-primary">
                  Create farm & continue <Icon name="arrow" size={16} />
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
