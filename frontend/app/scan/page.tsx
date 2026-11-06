"use client";

import Link from "next/link";
import { useRef, useState } from "react";

import {
  Badge,
  Field,
  Icon,
  PageHeader,
  Segmented,
  StatCard,
} from "@/components/workspace/ui";
import {
  ApiError,
  uploadImage,
  createObservation,
  type UploadDescriptor,
} from "@/lib/api";
import { readSession } from "@/lib/auth";

export default function ScanPage() {
  const [mediaType, setMediaType] = useState<"image" | "video">("image");
  const [cropCode, setCropCode] = useState("tomato");
  const [areaCode, setAreaCode] = useState("IND.33.18.01");
  const [notes, setNotes] = useState("");
  const [gps, setGps] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsStatus, setGpsStatus] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadDescriptor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const isAuth = !!readSession();

  function onFileSelected(files: FileList | null) {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  }

  function requestGps() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGpsStatus("Geolocation not supported by this browser.");
      return;
    }
    setGpsStatus("Acquiring GPS coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGps({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setGpsStatus(`Acquired ±${pos.coords.accuracy.toFixed(0)}m accuracy`);
      },
      (err) => {
        setGpsStatus(`Location unavailable (${err.message}). Using manual area code.`);
      },
      { timeout: 8000, enableHighAccuracy: true },
    );
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select an image or capture a photo first.");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // 1. Upload to backend /v1/uploads with quality checks
      const descriptor = await uploadImage(selectedFile);
      setUploadResult(descriptor);

      // 2. If authenticated, create real observation record
      if (isAuth) {
        try {
          await createObservation({
            client_report_id: `rep_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
            crop_code: cropCode,
            area_code: areaCode,
            notes: notes || undefined,
            captured_at: new Date().toISOString(),
          });
        } catch {
          // Observation creation may fail if consent missing, but upload succeeded
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.status} ${err.problem?.code ?? "upload_error"}: ${err.problem?.detail ?? err.message}`);
      } else {
        setError(err instanceof Error ? err.message : "Upload failed");
      }
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Field capture"
        title="Scan Plant & Upload Triage"
        lede="Capture canopy, foliage or stem photos with deterministic quality gating (sharpness, lighting, resolution) and provenance timestamps."
      />

      <div className="ws-stat-grid">
        <StatCard label="Capture mode" value={mediaType === "image" ? "Photo triage" : "Video reading"} detail="Spec 02/09 pipeline" icon="camera" tone="brand" />
        <StatCard label="Selected crop" value={cropCode.toUpperCase()} detail="Catalogue crop target" icon="leaf" tone="ok" />
        <StatCard label="Spatial unit" value={areaCode} detail="Administrative unit" icon="location" tone="default" />
      </div>

      <div className="ws-two-col">
        <form className="ws-panel" onSubmit={(e) => void handleSubmit(e)}>
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Input parameters</p>
              <h2>Capture context</h2>
            </div>
            <Segmented
              label="Capture media"
              value={mediaType}
              onChange={(val) => setMediaType(val as "image" | "video")}
              options={[
                { value: "image", label: "Photo" },
                { value: "video", label: "Video" },
              ]}
            />
          </div>

          <Field label="Target crop" hint="Must match open crop catalogue">
            <select
              className="ws-input"
              value={cropCode}
              onChange={(e) => setCropCode(e.target.value)}
              disabled={uploading}
            >
              <option value="tomato">Tomato (Solanum lycopersicum)</option>
              <option value="maize">Maize (Zea mays)</option>
              <option value="cotton">Cotton (Gossypium)</option>
              <option value="chilli">Chilli (Capsicum annuum)</option>
            </select>
          </Field>

          <Field label="Administrative Area Code" hint="Block or mandal identifier">
            <input
              type="text"
              className="ws-input"
              value={areaCode}
              onChange={(e) => setAreaCode(e.target.value)}
              disabled={uploading}
              required
            />
          </Field>

          <Field label="Field notes" hint="Visible signs, distribution across canopy">
            <textarea
              className="ws-textarea"
              rows={3}
              placeholder="e.g. Leaf curling and silvering on lower third of plants..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={uploading}
            />
          </Field>

          <div className="ws-field">
            <label className="ws-label">GPS coordinates (Optional)</label>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <button
                type="button"
                className="ws-button ws-button-secondary"
                onClick={requestGps}
                disabled={uploading}
              >
                <Icon name="location" size={16} /> Get GPS
              </button>
              {gps && (
                <span className="ws-small ws-mono">
                  {gps.lat.toFixed(4)}, {gps.lng.toFixed(4)}
                </span>
              )}
            </div>
            {gpsStatus && <p className="ws-small ws-muted" style={{ margin: "0.25rem 0 0" }}>{gpsStatus}</p>}
          </div>

          <div style={{ margin: "1.5rem 0" }}>
            <input
              ref={fileRef}
              type="file"
              accept={mediaType === "image" ? "image/jpeg,image/png,image/webp" : "video/mp4,video/webm"}
              style={{ display: "none" }}
              onChange={(e) => onFileSelected(e.target.files)}
            />

            <button
              type="button"
              className="ws-button ws-button-secondary"
              style={{ width: "100%", padding: "1.5rem", borderStyle: "dashed" }}
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              <Icon name="upload" size={24} />
              <span>{selectedFile ? `Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(0)} KB)` : "Choose or capture file"}</span>
            </button>
          </div>

          {error && (
            <div className="ws-notice ws-notice-bad" style={{ marginBottom: "1rem" }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          <button
            type="submit"
            className="ws-button ws-button-primary"
            style={{ width: "100%" }}
            disabled={uploading || !selectedFile}
          >
            {uploading ? "Uploading & running quality gate..." : "Upload & Analyze"}
          </button>
        </form>

        <section className="ws-panel">
          <div className="ws-panel-head">
            <div>
              <p className="ws-eyebrow">Quality assessment</p>
              <h2>Upload output</h2>
            </div>
            {uploadResult ? (
              <Badge tone="ok">{uploadResult.quality_result.toUpperCase()}</Badge>
            ) : (
              <Badge tone="neutral">Ready</Badge>
            )}
          </div>

          {uploadResult ? (
            <div>
              <div className="ws-notice ws-notice-ok" style={{ marginBottom: "1rem" }}>
                <strong>Quality gate passed:</strong> {uploadResult.quality_result}
              </div>

              <dl className="ws-detail-list">
                <div>
                  <dt>Upload ID</dt>
                  <dd className="ws-mono">{uploadResult.upload_id}</dd>
                </div>
                <div>
                  <dt>Dimensions</dt>
                  <dd>{uploadResult.width} × {uploadResult.height} px</dd>
                </div>
                <div>
                  <dt>Hash (SHA-256)</dt>
                  <dd className="ws-mono">{uploadResult.content_hash.slice(0, 16)}...</dd>
                </div>
                <div>
                  <dt>Quality flags</dt>
                  <dd>{uploadResult.quality_flags.length > 0 ? uploadResult.quality_flags.join(", ") : "None"}</dd>
                </div>
              </dl>

              <div className="ws-banner-actions" style={{ marginTop: "1.5rem" }}>
                <Link href="/analysis" className="ws-button ws-button-primary">
                  View in Observations
                </Link>
                <Link href="/chat" className="ws-button ws-button-secondary">
                  Chat triage
                </Link>
              </div>
            </div>
          ) : (
            <div>
              <p className="ws-muted">
                Images uploaded through this pipeline undergo automated checks for blur, minimum resolution, and contrast before being queued for model evaluation.
              </p>
              <div className="ws-notice ws-notice-info" style={{ marginTop: "1rem" }}>
                Per ADR-009, images are stored securely with short-lived presigned access URLs. No public S3 bucket is ever exposed.
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
