import Link from "next/link";

import { ApiError, getHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let service: string | null = null;
  let failure: string | null = null;

  try {
    const health = await getHealth();
    service = `${health.service} ${health.version} (${health.environment})`;
  } catch (error) {
    failure =
      error instanceof ApiError
        ? `${error.status} ${error.problem?.code ?? "api_error"}`
        : "API unreachable";
  }

  return (
    <>
      <h1>Crop early warning — platform foundation</h1>

      <section className="card" aria-labelledby="status-heading">
        <h2 id="status-heading">Platform status</h2>
        {service ? (
          <p>
            <span className="badge">API reachable</span> {service}
          </p>
        ) : (
          <p className="error">
            <span className="badge badge-muted">API unavailable</span> {failure}
          </p>
        )}
        <p className="muted">
          This page reports the platform state only. It does not report pest or
          disease risk.
        </p>
      </section>

      <section className="card" aria-labelledby="outputs-heading">
        <h2 id="outputs-heading">Two outputs, never merged</h2>
        <ul>
          <li>
            <strong>Photo assessment</strong> — what might be visible on one plant.
            Assistive, not a diagnosis.
          </li>
          <li>
            <strong>Area outlook</strong> — how likely a threat is in an area over a
            window. Arrives in a later phase; not shown here.
          </li>
        </ul>
        <p>
          <Link href="/chat">Open the photo-assessment chat</Link>
        </p>
      </section>

      <section className="card" aria-labelledby="demo-heading">
        <h2 id="demo-heading">Demo content</h2>
        <p>
          <span className="badge badge-muted">demo</span> The chat currently returns
          a labelled template reply. No image model is connected in this phase, and
          no assessment is fabricated.
        </p>
      </section>
    </>
  );
}
