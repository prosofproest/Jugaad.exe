import type { Assessment } from "@/lib/api";

const ABSTAIN_COPY: Record<string, string> = {
  below_class_threshold:
    "The evidence did not reach the threshold for any supported condition.",
  low_margin:
    "The leading candidates were too close to separate reliably.",
  high_entropy:
    "The visual evidence was too mixed to support one assessment.",
  out_of_distribution:
    "This image does not look like the photos the system was validated on.",
  unsupported_crop:
    "This crop is not on the supported list for this release.",
  quality_gate_failed:
    "The photo did not pass the image-quality check.",
  no_image: "No photo was attached, so there is nothing to assess.",
  demo_mode:
    "This is the scaffold demo: the image path is not connected to a model yet.",
};

const STATE_TITLE: Record<Assessment["state"], string> = {
  assessed: "Possible symptom match",
  abstained: "No assessment yet",
  unsupported_crop: "This crop is not supported yet",
  failed: "Could not assess this photo",
};

const CONFIDENCE_LABEL: Record<string, string> = {
  low: "low",
  medium: "medium",
  high: "high",
  not_calibrated: "not yet calibrated",
};

export function confidenceLabel(assessment: Assessment): string {
  if (!assessment.calibrated) {
    return "not yet calibrated";
  }
  return assessment.confidence_band
    ? (CONFIDENCE_LABEL[assessment.confidence_band] ?? assessment.confidence_band)
    : "not reported";
}

function reasonText(assessment: Assessment): string | null {
  if (assessment.reason_text) {
    return assessment.reason_text;
  }
  if (assessment.reason_code) {
    return ABSTAIN_COPY[assessment.reason_code] ?? null;
  }
  return null;
}

export function AssessmentCard({
  assessment,
  nextSteps,
  onRetake,
  onAddContext,
}: {
  assessment: Assessment;
  nextSteps: string[];
  onRetake?: () => void;
  onAddContext?: () => void;
}) {
  const isAssessed = assessment.state === "assessed";
  const candidates = assessment.candidates.slice(0, 3);
  const explanation = reasonText(assessment);
  const showRetake = nextSteps.includes("retake") || !isAssessed;
  const showAddContext = nextSteps.includes("add_context");

  return (
    <section className="assessment" aria-label="Photo assessment">
      <div>
        <p className="assessment-title">
          <strong>Photo assessment</strong>{" "}
          {assessment.is_demo ? (
            <span className="badge badge-muted">demo</span>
          ) : null}
        </p>
        <p className="assessment-state">{STATE_TITLE[assessment.state]}</p>
      </div>

      <p className="muted small">
        This is an assistive visual assessment, not a diagnosis or a laboratory
        result.
      </p>

      {isAssessed ? (
        <>
          {candidates.length > 0 ? (
            <>
              <p className="small">Top candidates, most likely first:</p>
              <ul className="assessment-candidates small">
                {candidates.map((candidate) => (
                  <li key={candidate.label}>
                    {candidate.label.replaceAll("_", " ")}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="small muted">No candidate list was returned.</p>
          )}
          <p className="small">
            Confidence: <strong>{confidenceLabel(assessment)}</strong>
            {assessment.calibrated
              ? "."
              : " — shown as a band only; probabilities are not validated for display."}
          </p>
        </>
      ) : explanation ? (
        <p className="small">{explanation}</p>
      ) : null}

      {(showRetake || showAddContext) && (
        <div className="chip-row">
          {showRetake && onRetake ? (
            <button type="button" className="button-secondary" onClick={onRetake}>
              Retake photo
            </button>
          ) : null}
          {showAddContext && onAddContext ? (
            <button type="button" className="button-secondary" onClick={onAddContext}>
              Add context
            </button>
          ) : null}
        </div>
      )}

      {nextSteps.includes("request_review") ||
      nextSteps.includes("read_advisory") ? (
        <p className="small muted">
          Expert review and approved advisories arrive in a later phase. This reply
          does not include them.
        </p>
      ) : null}

      <div className="assessment-footer">
        <span className="mono">Model: {assessment.model_version}</span>
        <span>
          Generated{" "}
          <time dateTime={assessment.generated_at}>
            {new Date(assessment.generated_at).toLocaleString()}
          </time>
        </span>
        <span>
          Calibration: {assessment.calibrated ? "calibrated" : "not yet calibrated"}
        </span>
      </div>
    </section>
  );
}
