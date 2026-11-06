"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import {
  EmptyState,
  Icon,
  PageHeader,
} from "@/components/workspace/ui";
import { useWorkspace } from "@/lib/workspace/store";

export default function FarmDetailPage() {
  const params = useParams();
  const farmId = typeof params?.id === "string" ? params.id : "";
  const { state } = useWorkspace();
  const farm = state.farms.find((item) => item.id === farmId);

  return (
    <div className="ws-page">
      <PageHeader
        eyebrow="Farm detail"
        title={farm ? farm.name : "Farm record"}
        lede="Cadastral farm detail views are awaiting the backend farm management service."
        actions={
          <Link href="/farms" className="ws-button ws-button-secondary">
            <Icon name="arrow" size={16} /> Back to farms
          </Link>
        }
      />

      <div className="ws-banner ws-banner-warn">
        <Icon name="alert" size={18} />
        <div>
          <strong>Backend capability pending (`/v1/farms/{farmId || "{id}"}`)</strong>
          <p>
            The backend does not yet support retrieving individual farm boundaries or plots.
            Area scouting and observations are conducted at the administrative block level.
          </p>
        </div>
      </div>

      <EmptyState
        title="Farm record not accessible"
        body="No backend endpoint is available to query individual farm polygons or crop cycles. Please refer to administrative area scouting."
        action={
          <Link href="/farms" className="ws-button ws-button-primary">
            View farms overview
          </Link>
        }
      />
    </div>
  );
}
