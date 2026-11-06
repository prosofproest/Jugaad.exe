import type { Metadata } from "next";

import { AuthGate } from "@/components/auth-gate";
import { OutlookClient } from "@/components/outlook-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Area outlook",
};

export default function OutlookPage() {
  return (
    <AuthGate>
      <OutlookClient />
    </AuthGate>
  );
}
