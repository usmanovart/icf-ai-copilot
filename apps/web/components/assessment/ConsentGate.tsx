"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { AlertTriangle, Shield } from "lucide-react";

interface ConsentGateProps {
  children: React.ReactNode;
}

const CONSENT_DOCUMENT_VERSION = "1.0";

const WELLBEING_DISCLAIMER = `
ICF AI Copilot is a personal development and decision-support tool.
It is not a medical, psychological, or clinical service.
None of the assessments, insights, or recommendations constitute medical advice.
If you are experiencing significant distress, please consult a qualified professional.
`.trim();

const DATA_USES = {
  ai_processing: true,
  org_sharing: false,
  anonymous_research: false,
};

/**
 * ConsentGate — renders children only when the user has an active consent record.
 * Shows a consent capture screen otherwise.
 */
export function ConsentGate({ children }: ConsentGateProps) {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<"loading" | "consented" | "required">("loading");
  const [submitting, setSubmitting] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    checkConsent();
  }, []);

  async function checkConsent() {
    try {
      const token = await getToken();
      const res = await fetch("/api/v1/consent/current", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data ? "consented" : "required");
      } else {
        setStatus("required");
      }
    } catch {
      setStatus("required");
    }
  }

  async function handleConsent() {
    if (!checked) return;
    setSubmitting(true);
    try {
      const token = await getToken();
      const res = await fetch("/api/v1/consent/record", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          version: CONSENT_DOCUMENT_VERSION,
          data_uses: DATA_USES,
        }),
      });
      if (res.ok) {
        setStatus("consented");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (status === "loading") {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (status === "consented") {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-8 shadow-sm">
        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold">Before we begin</h1>
            <p className="text-sm text-muted-foreground">Your privacy and wellbeing come first</p>
          </div>
        </div>

        {/* Wellbeing disclaimer */}
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-600" />
            <p className="text-sm text-amber-800">{WELLBEING_DISCLAIMER}</p>
          </div>
        </div>

        {/* What we collect */}
        <div className="mb-6 space-y-3 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">What ICF AI Copilot does with your data:</p>
          <ul className="space-y-2">
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-green-600">✓</span>
              Uses your assessment responses to generate a personalised AI profile
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-green-600">✓</span>
              Stores your profile to provide contextual AI recommendations
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-green-600">✓</span>
              Logs all AI interactions for explainability and your review
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-red-500">✗</span>
              Does not share your individual data with your organisation without your explicit consent
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-red-500">✗</span>
              Does not sell or transfer your data to third parties
            </li>
          </ul>
          <p>
            You can withdraw consent at any time from your account settings.
            Withdrawal triggers anonymisation of your data.
          </p>
        </div>

        {/* Consent checkbox */}
        <label className="mb-6 flex cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-border accent-primary"
          />
          <span className="text-sm text-foreground">
            I have read and understood the information above and consent to ICF AI Copilot
            processing my assessment data to generate my profile and personalised recommendations.
          </span>
        </label>

        <button
          onClick={handleConsent}
          disabled={!checked || submitting}
          className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-50"
        >
          {submitting ? "Recording consent…" : "I consent — continue to assessment"}
        </button>
      </div>
    </div>
  );
}
