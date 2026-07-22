"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  Brain,
  Target,
  Zap,
  TrendingUp,
  AlertCircle,
  Lightbulb,
  RefreshCw,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { DomainRadarChart, DomainScore } from "@/components/profile/DomainRadarChart";
import { ProfileInsightCard } from "@/components/profile/ProfileInsightCard";
import { WellbeingDisclaimer } from "@/components/shared/WellbeingDisclaimer";
import { cn } from "@/lib/utils";

// ── Types matching ProfileOut from schemas.py ──────────────────────────────────

interface MindData {
  stress_score?: number;
  stress_level?: string;
  big_five?: Record<string, number>;
  big_five_labels?: Record<string, string>;
}

interface GoalData {
  goal_clarity?: number;
  motivation_type?: string;
  top_goals?: string[];
}

interface WorkCapacityData {
  burnout_risk?: string;
  exhaustion_score?: number;
  engagement_score?: number;
  cynicism_score?: number;
}

interface ProfileData {
  id: string;
  version: number;
  is_active: boolean;
  mind_data: MindData | null;
  goal_data: GoalData | null;
  work_capacity_data: WorkCapacityData | null;
  summary_text: string | null;
  strengths: Array<{ label: string; description?: string; framework_ref?: string }> | null;
  risks: Array<{ label: string; description?: string; framework_ref?: string }> | null;
  opportunities: Array<{ label: string; description?: string; framework_ref?: string }> | null;
  created_at: string;
}

// ── Domain score builder ────────────────────────────────────────────────────────

function buildDomainScores(profile: ProfileData): DomainScore[] {
  const scores: DomainScore[] = [];

  // Mind — stress (inverted, lower stress = higher score)
  const stressRaw = profile.mind_data?.stress_score ?? null;
  scores.push({
    domain: "mind_stress",
    label: "Stress",
    // invert: stress_score is 0-100 where 100 = maximum stress
    score: stressRaw !== null ? Math.round(100 - stressRaw) : 50,
    color: "#7c5cd8",
  });

  // Mind — Big Five average
  const bigFive = profile.mind_data?.big_five;
  const bigFiveAvg = bigFive
    ? Math.round(
        Object.values(bigFive).reduce((a, b) => a + b, 0) /
          Object.values(bigFive).length
      )
    : 50;
  scores.push({
    domain: "mind_personality",
    label: "Personality",
    score: bigFiveAvg,
    color: "#3b82d4",
  });

  // Goal clarity
  scores.push({
    domain: "goal_clarity",
    label: "Goal Clarity",
    score: Math.round((profile.goal_data?.goal_clarity ?? 0.5) * 100),
    color: "#10b981",
  });

  // Work capacity — engagement (inverted burnout)
  const burnoutScoreMap: Record<string, number> = { low: 80, moderate: 55, high: 30, critical: 10 };
  const burnoutRisk = profile.work_capacity_data?.burnout_risk ?? "moderate";
  const burnoutScore = burnoutScoreMap[burnoutRisk] ?? 55;
  scores.push({
    domain: "work_capacity",
    label: "Work Capacity",
    score: burnoutScore,
    color: "#f59e0b",
  });

  // Engagement score
  scores.push({
    domain: "engagement",
    label: "Engagement",
    score: Math.round((profile.work_capacity_data?.engagement_score ?? 0.5) * 100),
    color: "#ef4444",
  });

  // Resilience — derived from stress + burnout composite
  const resilienceRaw =
    ((100 - (stressRaw ?? 50)) + burnoutScore) / 2;
  scores.push({
    domain: "resilience",
    label: "Resilience",
    score: Math.round(resilienceRaw),
    color: "#06b6d4",
  });

  return scores;
}

// ── Burnout risk badge ──────────────────────────────────────────────────────────

const BURNOUT_MAP: Record<string, { label: string; cls: string }> = {
  low:      { label: "Low Risk",               cls: "bg-green-100 text-green-700 border-green-200" },
  moderate: { label: "Moderate Risk",           cls: "bg-amber-100 text-amber-700 border-amber-200" },
  high:     { label: "High Risk",               cls: "bg-orange-100 text-orange-700 border-orange-200" },
  critical: { label: "Critical — Seek Support", cls: "bg-red-100 text-red-700 border-red-200" },
};

const BURNOUT_FALLBACK = BURNOUT_MAP["moderate"]!;

function BurnoutBadge({ risk }: { risk?: string }) {
  const entry = (risk ? BURNOUT_MAP[risk] : undefined) ?? BURNOUT_FALLBACK;
  return (
    <span
      className={cn(
        "inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        entry.cls
      )}
    >
      {entry.label}
    </span>
  );
}

// ── Big Five bar ────────────────────────────────────────────────────────────────

const BIG_FIVE_META: Record<string, { label: string; description: string }> = {
  openness:          { label: "Openness",          description: "Curiosity and creativity" },
  conscientiousness: { label: "Conscientiousness", description: "Organisation and discipline" },
  extraversion:      { label: "Extraversion",      description: "Social energy and assertiveness" },
  agreeableness:     { label: "Agreeableness",     description: "Cooperation and empathy" },
  neuroticism:       { label: "Emotional Stability", description: "Stress tolerance (inverted N)" },
};

function BigFiveBar({ trait, score }: { trait: string; score: number }) {
  const meta = BIG_FIVE_META[trait] ?? { label: trait, description: "" };
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-foreground">{meta.label}</span>
        <span className="text-muted-foreground">{score}/100</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-700"
          style={{ width: `${score}%` }}
          role="progressbar"
          aria-valuenow={score}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <p className="text-xs text-muted-foreground">{meta.description}</p>
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────────

/**
 * ProfilePageContent — the full profile view.
 * Rendered inside app/(user)/profile/page.tsx after data fetch.
 */
export function ProfilePageContent() {
  const { getToken } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "empty" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    setStatus("loading");
    try {
      const token = await getToken();
      const res = await fetch("/api/v1/profiles/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 404) {
        setStatus("empty");
        return;
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `API error ${res.status}`);
      }
      const data: ProfileData = await res.json();
      setProfile(data);
      setStatus("ready");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Unknown error");
      setStatus("error");
    }
  }

  // ── Loading ──
  if (status === "loading") {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  // ── Error ──
  if (status === "error") {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 text-center">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-muted-foreground">{errorMsg}</p>
        <button
          onClick={loadProfile}
          className="text-sm text-primary underline-offset-4 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  // ── Empty ──
  if (status === "empty" || !profile) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4 text-center">
        <Brain className="h-12 w-12 text-muted-foreground/40" />
        <div>
          <p className="font-semibold text-foreground">No profile yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Complete your assessment to generate your AI profile.
          </p>
        </div>
        <a
          href="/assessment"
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
        >
          Start Assessment
        </a>
      </div>
    );
  }

  const domainScores = buildDomainScores(profile);
  const bigFive = profile.mind_data?.big_five ?? {};
  const createdAt = new Date(profile.created_at).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="space-y-8">

      {/* ── Header ── */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">My Profile</h1>
          <p className="mt-1 text-sm text-muted-foreground flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            Generated {createdAt} · Version {profile.version}
            <span className="ml-1 inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">
              <CheckCircle2 className="h-3 w-3" /> Active
            </span>
          </p>
        </div>
        <button
          onClick={loadProfile}
          className="flex items-center gap-2 self-start rounded-md border border-border px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent sm:self-auto"
          aria-label="Refresh profile"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {/* ── Wellbeing Disclaimer ── */}
      <WellbeingDisclaimer variant="inline" />

      {/* ── Summary ── */}
      {profile.summary_text && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="h-4 w-4 text-primary" />
            <h2 className="font-semibold text-foreground">AI Profile Summary</h2>
            <span className="ml-auto rounded bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
              IBM Granite
            </span>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {profile.summary_text}
          </p>
        </div>
      )}

      {/* ── Radar + Work Capacity ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* Radar Chart */}
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-4 font-semibold text-foreground flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Human Development Profile
          </h2>
          <DomainRadarChart scores={domainScores} size={300} />
          <p className="mt-2 text-center text-xs text-muted-foreground">
            ICF 6-Domain Assessment · Scores 0–100
          </p>
        </div>

        {/* Work Capacity Detail */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h2 className="font-semibold text-foreground flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-500" />
            Work Capacity
          </h2>

          {/* Burnout risk */}
          <div>
            <p className="text-xs text-muted-foreground mb-1.5 uppercase tracking-wide font-medium">
              Burnout Risk
            </p>
            <BurnoutBadge risk={profile.work_capacity_data?.burnout_risk} />
          </div>

          {/* Engagement */}
          {profile.work_capacity_data?.engagement_score !== undefined && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">
                Engagement
              </p>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-green-500"
                  style={{
                    width: `${Math.round(
                      profile.work_capacity_data.engagement_score * 100
                    )}%`,
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {Math.round(profile.work_capacity_data.engagement_score * 100)}/100
              </p>
            </div>
          )}

          {/* Goal motivation */}
          {profile.goal_data?.motivation_type && (
            <div>
              <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wide font-medium">
                Motivation Type
              </p>
              <p className="text-sm font-medium text-foreground capitalize">
                {profile.goal_data.motivation_type}
              </p>
              <p className="text-xs text-muted-foreground">
                Self-Determination Theory (Deci & Ryan, 2000)
              </p>
            </div>
          )}

          {/* Goal clarity */}
          {profile.goal_data?.goal_clarity !== undefined && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">
                Goal Clarity
              </p>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{
                    width: `${Math.round(profile.goal_data.goal_clarity * 100)}%`,
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {Math.round(profile.goal_data.goal_clarity * 100)}/100
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Big Five Personality ── */}
      {Object.keys(bigFive).length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-4 font-semibold text-foreground flex items-center gap-2">
            <Brain className="h-4 w-4 text-primary" />
            Personality Profile
            <span className="ml-auto text-xs font-normal text-muted-foreground">
              Big Five · IPIP Norms
            </span>
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {Object.entries(bigFive).map(([trait, score]) => (
              <BigFiveBar
                key={trait}
                trait={trait}
                score={typeof score === "number" ? Math.round(score) : 50}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Strengths / Risks / Opportunities ── */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
        <ProfileInsightCard
          title="Strengths"
          icon={TrendingUp}
          iconColorClass="bg-green-100 text-green-600"
          items={profile.strengths ?? []}
          emptyMessage="Complete your assessment to identify your strengths."
        />
        <ProfileInsightCard
          title="Risks & Bottlenecks"
          icon={AlertCircle}
          iconColorClass="bg-red-100 text-red-600"
          items={profile.risks ?? []}
          emptyMessage="No risks identified."
        />
        <ProfileInsightCard
          title="Opportunities"
          icon={Lightbulb}
          iconColorClass="bg-amber-100 text-amber-600"
          items={profile.opportunities ?? []}
          emptyMessage="No opportunities identified yet."
        />
      </div>

      {/* ── Explainability footer ── */}
      <div className="rounded-xl border border-border bg-muted/30 p-4">
        <div className="flex items-start gap-3">
          <Target className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
          <div className="text-xs text-muted-foreground space-y-1">
            <p className="font-medium text-foreground text-sm">How this profile was generated</p>
            <p>
              Your responses were scored using validated psychological frameworks
              (PSS-10, IPIP Big Five, Maslach Burnout Inventory, Self-Determination Theory).
              IBM Granite synthesised the narrative summary and insights via a structured
              LangChain LCEL pipeline. All inference is logged in the AI audit trail.
            </p>
            <p className="font-medium">
              This profile is for personal development only and does not constitute
              medical, clinical, or psychiatric assessment.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}
