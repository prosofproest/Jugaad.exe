"use client";

import Link from "next/link";
import { useState } from "react";

import {
  Badge,
  Field,
  HealthPill,
  Icon,
  Modal,
  PageHeader,
  ProgressBar,
  StatCard,
} from "@/components/workspace/ui";
import { formatAcres, formatDate } from "@/lib/format";
import { cropGroupHealth, useWorkspace } from "@/lib/workspace/store";
import type { Health } from "@/lib/workspace/types";

export default function FarmsPage() {
  const { state, addFarm } = useWorkspace();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({
    name: "",
    village: "",
    district: "Krishnagiri",
    areaAcres: "2",
    crop: "Tomato",
    variety: "Arka Rakshak",
    soil: "Red loam",
    irrigation: "Drip",
    lat: "12.7409",
    lng: "77.8253",
  });
  const [gpsStatus, setGpsStatus] = useState("");

  const farms = state.farms.filter((farm) =>
    `${farm.name} ${farm.village} ${farm.district}`.toLowerCase().includes(query.toLowerCase()),
  );

  const totalAcres = state.farms.reduce((sum, farm) => sum + farm.areaAcres, 0);
  const crops = new Set(state.cropGroups.map((group) => group.crop));

  function useGps() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGpsStatus("GPS is not available in this browser. Demo coordinates kept.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setForm((current) => ({
          ...current,
          lat: position.coords.latitude.toFixed(5),
          lng: position.coords.longitude.toFixed(5),
        }));
        setGpsStatus("GPS captured with permission.");
      },
      () => setGpsStatus("Permission denied. Type coordinates or keep the demo location."),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.name.trim()) return;
    addFarm({
      name: form.name.trim(),
      village: form.village || "Hosur",
      district: form.district,
      areaAcres: Number(form.areaAcres) || 1,
      crop: form.crop,
      variety: form.variety || "Local",
      lat: Number(form.lat) || 12.7409,
      lng: Number(form.lng) || 77.8253,
      soil: form.soil,
      irrigation: form.irrigation,
    });
    setOpen(false);
    setForm((current) => ({ ...current, name: "", village: "" }));
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Farm management"
        title="Farms, plots and crops"
        lede="Register farm details, capture GPS boundaries, divide land into plots and sections, and track every crop group."
        actions={
          <button type="button" className="ws-button ws-button-primary" onClick={() => setOpen(true)}>
            <Icon name="plus" size={17} /> Add new farm
          </button>
        }
      />

      <div className="ws-stat-grid">
        <StatCard label="Farms" value={state.farms.length} detail={`${totalAcres.toFixed(1)} acres total`} icon="farm" tone="brand" />
        <StatCard label="Plots" value={state.plots.length} detail={`${state.plots.reduce((sum, plot) => sum + plot.sections.length, 0)} sections`} icon="map" />
        <StatCard label="Crop groups" value={state.cropGroups.length} detail={`${crops.size} crop types`} icon="leaf" />
        <StatCard label="Plants with IDs" value={state.plants.length} detail="Individual plant tracking" icon="plant" tone="ok" />
      </div>

      <div className="ws-toolbar">
        <label className="ws-search">
          <Icon name="search" size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search farm, village or district"
            aria-label="Search farms"
          />
        </label>
        <div className="ws-chip-row">
          <span className="ws-chip"><Icon name="location" size={14} /> GPS boundaries</span>
          <span className="ws-chip"><Icon name="water" size={14} /> Irrigation records</span>
          <span className="ws-chip"><Icon name="plant" size={14} /> Plant-level IDs</span>
        </div>
      </div>

      <div className="ws-farm-grid">
        {farms.map((farm) => {
          const plots = state.plots.filter((plot) => plot.farmId === farm.id);
          const groups = state.cropGroups.filter((group) => group.farmId === farm.id);
          const plants = state.plants.filter((plant) => plant.farmId === farm.id);
          const healthy = plants.filter((plant) => plant.health === "healthy").length;
          const worst: Health =
            plants.some((plant) => plant.health === "pest")
              ? "pest"
              : plants.some((plant) => plant.health === "diseased")
                ? "diseased"
                : plants.some((plant) => plant.health === "watch")
                  ? "watch"
                  : "healthy";
          return (
            <article key={farm.id} className="ws-farm-card">
              <div className="ws-farm-card-head">
                <div>
                  <p className="ws-eyebrow">{farm.village} · {farm.district}</p>
                  <h2>{farm.name}</h2>
                  <p className="ws-small ws-muted">{formatAcres(farm.areaAcres)}</p>
                </div>
                <HealthPill health={worst} />
              </div>

              <div className="ws-farm-thumb">
                <svg viewBox="0 0 100 44" aria-hidden="true">
                  {plots.map((plot, index) => (
                    <rect
                      key={plot.id}
                      x={6 + (index % 3) * 30}
                      y={5 + Math.floor(index / 3) * 18}
                      width="26"
                      height="14"
                      rx="2"
                      className={`ws-farm-thumb-plot ws-health-${plot.health}`}
                    />
                  ))}
                  <path d="M2 40 C 24 34, 52 42, 98 34" className="ws-farm-thumb-road" fill="none" />
                </svg>
                <span className="ws-farm-gps">
                  <Icon name="location" size={13} /> {farm.lat.toFixed(4)}, {farm.lng.toFixed(4)}
                </span>
              </div>

              <div className="ws-farm-meta">
                <div><span>Plots</span><strong>{plots.length}</strong></div>
                <div><span>Crop groups</span><strong>{groups.length}</strong></div>
                <div><span>Plants</span><strong>{plants.length}</strong></div>
                <div><span>Soil</span><strong>{farm.soil}</strong></div>
              </div>

              <ProgressBar
                value={plants.length > 0 ? Math.round((healthy / plants.length) * 100) : 100}
                label={`${healthy} of ${plants.length} plants healthy`}
                tone={worst === "healthy" ? "ok" : worst === "watch" ? "warn" : "bad"}
              />

              <div className="ws-chip-row">
                {groups.slice(0, 3).map((group) => (
                  <span key={group.id} className="ws-chip">
                    {group.crop} · {cropGroupHealth(state, group.id).replace("_", " ")}
                  </span>
                ))}
                {groups.length > 3 ? <span className="ws-chip ws-chip-muted">+{groups.length - 3} more</span> : null}
              </div>

              <div className="ws-farm-card-foot">
                <span className="ws-small ws-muted">Added {formatDate(farm.createdAt)}</span>
                <div>
                  <Link href={`/map?farm=${farm.id}`} className="ws-button ws-button-ghost">
                    <Icon name="map" size={15} /> Map
                  </Link>
                  <Link href={`/farms/${farm.id}`} className="ws-button ws-button-secondary">
                    Open farm <Icon name="arrow" size={15} />
                  </Link>
                </div>
              </div>
            </article>
          );
        })}

        <button type="button" className="ws-farm-add" onClick={() => setOpen(true)}>
          <span className="ws-empty-icon"><Icon name="plus" size={24} /></span>
          <strong>Add another farm</strong>
          <span>Register name, GPS location, boundary and area.</span>
        </button>
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Register a new farm"
        footer={
          <>
            <button type="button" className="ws-button ws-button-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button type="submit" form="farm-form" className="ws-button ws-button-primary">
              <Icon name="plus" size={16} /> Create farm
            </button>
          </>
        }
      >
        <form id="farm-form" onSubmit={submit} className="ws-form">
          <Field label="Farm name">
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Sunrise Farm" required />
          </Field>
          <div className="ws-form-grid">
            <Field label="Village">
              <input value={form.village} onChange={(event) => setForm({ ...form, village: event.target.value })} placeholder="Hosur" />
            </Field>
            <Field label="District">
              <select value={form.district} onChange={(event) => setForm({ ...form, district: event.target.value })}>
                <option>Krishnagiri</option>
                <option>Dharmapuri</option>
                <option>Salem</option>
              </select>
            </Field>
          </div>
          <div className="ws-form-grid">
            <Field label="Area (acres)" hint="Hectares are shown alongside acres.">
              <input
                type="number"
                min="0.1"
                step="0.1"
                value={form.areaAcres}
                onChange={(event) => setForm({ ...form, areaAcres: event.target.value })}
              />
            </Field>
            <Field label="Soil type">
              <select value={form.soil} onChange={(event) => setForm({ ...form, soil: event.target.value })}>
                <option>Red loam</option>
                <option>Sandy clay</option>
                <option>Black cotton</option>
                <option>Alluvial</option>
              </select>
            </Field>
          </div>
          <div className="ws-form-grid">
            <Field label="Main crop">
              <select value={form.crop} onChange={(event) => setForm({ ...form, crop: event.target.value })}>
                <option>Tomato</option>
                <option>Chilli</option>
                <option>Brinjal</option>
                <option>Mango</option>
                <option>Maize</option>
                <option>Cowpea</option>
                <option>Beans</option>
              </select>
            </Field>
            <Field label="Variety">
              <input value={form.variety} onChange={(event) => setForm({ ...form, variety: event.target.value })} />
            </Field>
          </div>
          <Field label="Irrigation">
            <select value={form.irrigation} onChange={(event) => setForm({ ...form, irrigation: event.target.value })}>
              <option>Drip</option>
              <option>Sprinkler</option>
              <option>Canal</option>
              <option>Rain-fed</option>
            </select>
          </Field>
          <div className="ws-gps-box">
            <div>
              <strong>Farm location & boundary</strong>
              <p className="ws-small ws-muted">{form.lat}, {form.lng}</p>
              {gpsStatus ? <p className="ws-small">{gpsStatus}</p> : null}
            </div>
            <button type="button" className="ws-button ws-button-secondary" onClick={useGps}>
              <Icon name="location" size={16} /> Capture GPS
            </button>
          </div>
          <p className="ws-small ws-muted">
            A default rectangular boundary is created from these coordinates. You can adjust the
            boundary and divide the farm into plots and sections after saving.
          </p>
          <div className="ws-form-actions">
            <Badge tone="neutral">Demo data</Badge>
            <span className="ws-small ws-muted">Stored on this device</span>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export type { Health };
