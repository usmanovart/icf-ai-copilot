"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { ChevronRight, ChevronLeft, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Question {
  key: string;
  text: string;
  type: "likert5" | "scale10";
  labels?: string[];
  min_label?: string;
  max_label?: string;
}

interface Module {
  module_id: string;
  domain: string;
  title: string;
  description: string;
  estimated_minutes: number;
  disclaimer?: string;
  question_count: number;
}

interface ModuleDetail extends Module {
  questions: Question[];
}

const MODULE_ORDER = [
  "mind_stress",
  "mind_big_five",
  "goal_clarity",
  "work_capacity_burnout",
];

/**
 * Full assessment flow: intro → questions → completion.
 */
export function AssessmentFlow() {
  const { getToken } = useAuth();
  const router = useRouter();

  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
  const [currentModuleDetail, setCurrentModuleDetail] = useState<ModuleDetail | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [phase, setPhase] = useState<"intro" | "questions" | "module_complete" | "done">("intro");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    initAssessment();
  }, []);

  async function initAssessment() {
    const token = await getToken();
    const headers = { Authorization: `Bearer ${token}` };

    // Load modules list
    const modRes = await fetch("/api/v1/assessments/modules", { headers });
    const modData = await modRes.json();
    const orderedModules = MODULE_ORDER
      .map((id) => modData.modules.find((m: Module) => m.module_id === id))
      .filter(Boolean) as Module[];
    setModules(orderedModules);

    // Start assessment session
    const startRes = await fetch("/api/v1/assessments/start", {
      method: "POST",
      headers,
    });
    const startData = await startRes.json();
    setAssessmentId(startData.id);
    setLoading(false);
  }

  async function loadModuleDetail(moduleId: string) {
    const token = await getToken();
    const res = await fetch(`/api/v1/assessments/modules/${moduleId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    setCurrentModuleDetail(data);
    setCurrentQuestionIndex(0);
    setPhase("questions");
  }

  function handleAnswer(questionKey: string, value: number) {
    setAnswers((prev) => ({ ...prev, [questionKey]: value }));
  }

  async function submitModule() {
    if (!assessmentId || !currentModuleDetail) return;
    setSubmitting(true);

    const token = await getToken();
    const responses = currentModuleDetail.questions.map((q) => ({
      module_id: currentModuleDetail.module_id,
      question_key: q.key,
      response_value: answers[q.key] ?? 0,
    }));

    await fetch(`/api/v1/assessments/${assessmentId}/respond`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(responses),
    });

    setSubmitting(false);
    setPhase("module_complete");
  }

  async function proceedToNextModule() {
    const nextIndex = currentModuleIndex + 1;
    if (nextIndex < modules.length) {
      setCurrentModuleIndex(nextIndex);
      await loadModuleDetail(modules[nextIndex]!.module_id);
    } else {
      await completeAssessment();
    }
  }

  async function completeAssessment() {
    if (!assessmentId) return;
    setSubmitting(true);
    const token = await getToken();
    await fetch(`/api/v1/assessments/${assessmentId}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    setSubmitting(false);
    setPhase("done");
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  /* ── Intro ────────────────────────────────────────────── */
  if (phase === "intro") {
    return (
      <div className="mx-auto max-w-xl py-10 px-4">
        <h1 className="text-2xl font-bold mb-2">Your Decision Intelligence Assessment</h1>
        <p className="text-muted-foreground mb-8 text-sm">
          {modules.length} modules · ~{modules.reduce((s, m) => s + m.estimated_minutes, 0)} minutes total
        </p>
        <div className="space-y-3 mb-8">
          {modules.map((mod, i) => (
            <div key={mod.module_id} className="flex items-center gap-3 rounded-lg border border-border p-4">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                {i + 1}
              </div>
              <div>
                <p className="text-sm font-semibold">{mod.title}</p>
                <p className="text-xs text-muted-foreground">{mod.description.slice(0, 80)}…</p>
              </div>
              <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
                ~{mod.estimated_minutes} min
              </span>
            </div>
          ))}
        </div>
        <button
          onClick={() => loadModuleDetail(modules[0]!.module_id)}
          className="w-full rounded-md bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground"
        >
          Begin Assessment <ChevronRight className="ml-1 inline h-4 w-4" />
        </button>
      </div>
    );
  }

  /* ── Questions ────────────────────────────────────────── */
  if (phase === "questions" && currentModuleDetail) {
    const questions = currentModuleDetail.questions;
    const question = questions[currentQuestionIndex]!;
    const progress = ((currentModuleIndex) / modules.length) * 100;
    const answered = answers[question.key] !== undefined;

    return (
      <div className="mx-auto max-w-xl py-10 px-4">
        {/* Module progress */}
        <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
          <span>{currentModuleDetail.title}</span>
          <span>Module {currentModuleIndex + 1} of {modules.length}</span>
        </div>
        <div className="mb-6 h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${progress + (currentQuestionIndex / questions.length) * (100 / modules.length)}%` }}
          />
        </div>

        {/* Disclaimer banner */}
        {currentModuleDetail.disclaimer && currentQuestionIndex === 0 && (
          <div className="mb-5 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            {currentModuleDetail.disclaimer}
          </div>
        )}

        {/* Question */}
        <p className="mb-1 text-xs text-muted-foreground">
          Question {currentQuestionIndex + 1} of {questions.length}
        </p>
        <h2 className="mb-6 text-lg font-semibold leading-snug">{question.text}</h2>

        {/* Likert response */}
        {question.type === "likert5" && question.labels && (
          <div className="grid grid-cols-5 gap-2 mb-8">
            {question.labels.map((label, idx) => (
              <button
                key={idx}
                onClick={() => handleAnswer(question.key, idx)}
                className={cn(
                  "flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center text-xs transition-all",
                  answers[question.key] === idx
                    ? "border-primary bg-primary/10 font-semibold text-primary"
                    : "border-border hover:border-primary/50 hover:bg-accent"
                )}
              >
                <span className="text-base font-bold">{idx + 1}</span>
                <span className="leading-tight">{label}</span>
              </button>
            ))}
          </div>
        )}

        {/* Scale 1-10 response */}
        {question.type === "scale10" && (
          <div className="mb-8">
            <div className="flex justify-between text-xs text-muted-foreground mb-2">
              <span>{question.min_label}</span>
              <span>{question.max_label}</span>
            </div>
            <div className="flex gap-1.5">
              {Array.from({ length: 10 }, (_, i) => i + 1).map((val) => (
                <button
                  key={val}
                  onClick={() => handleAnswer(question.key, val - 1)}
                  className={cn(
                    "flex-1 rounded border py-2 text-sm font-semibold transition-all",
                    answers[question.key] === val - 1
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3">
          {currentQuestionIndex > 0 && (
            <button
              onClick={() => setCurrentQuestionIndex((i) => i - 1)}
              className="flex items-center gap-1 rounded-md border border-border px-4 py-2 text-sm font-medium"
            >
              <ChevronLeft className="h-4 w-4" /> Back
            </button>
          )}
          <button
            disabled={!answered}
            onClick={() => {
              if (currentQuestionIndex < questions.length - 1) {
                setCurrentQuestionIndex((i) => i + 1);
              } else {
                submitModule();
              }
            }}
            className="ml-auto flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
          >
            {currentQuestionIndex < questions.length - 1 ? (
              <><span>Next</span><ChevronRight className="h-4 w-4" /></>
            ) : submitting ? (
              "Saving…"
            ) : (
              "Complete module"
            )}
          </button>
        </div>
      </div>
    );
  }

  /* ── Module complete ──────────────────────────────────── */
  if (phase === "module_complete") {
    const isLastModule = currentModuleIndex >= modules.length - 1;
    return (
      <div className="mx-auto max-w-sm py-16 px-4 text-center">
        <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-500" />
        <h2 className="text-xl font-bold mb-2">{currentModuleDetail?.title} complete</h2>
        <p className="text-muted-foreground text-sm mb-8">
          {isLastModule
            ? "That's the last module. We're now generating your AI profile."
            : `${modules.length - currentModuleIndex - 1} module${modules.length - currentModuleIndex - 1 !== 1 ? "s" : ""} remaining.`}
        </p>
        <button
          onClick={proceedToNextModule}
          disabled={submitting}
          className="w-full rounded-md bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground disabled:opacity-50"
        >
          {submitting
            ? "Generating your profile…"
            : isLastModule
            ? "Generate my profile"
            : "Continue to next module"}
        </button>
      </div>
    );
  }

  /* ── Done ─────────────────────────────────────────────── */
  if (phase === "done") {
    return (
      <div className="mx-auto max-w-sm py-16 px-4 text-center">
        <CheckCircle className="mx-auto mb-4 h-14 w-14 text-green-500" />
        <h2 className="text-2xl font-bold mb-2">Profile ready</h2>
        <p className="text-muted-foreground text-sm mb-8">
          Your AI Decision Profile has been generated. Let's take a look.
        </p>
        <button
          onClick={() => router.push("/profile")}
          className="w-full rounded-md bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground"
        >
          View my profile <ChevronRight className="inline h-4 w-4" />
        </button>
      </div>
    );
  }

  return null;
}
