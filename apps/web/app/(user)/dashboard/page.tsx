/**
 * Dashboard page — placeholder for Sub-Task 6.
 * Shows a minimal welcome state until widgets are built.
 */
export default function DashboardPage() {
  return (
    <div className="p-6 md:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Welcome to ICF AI Copilot. Complete your assessment to get started.
        </p>
      </div>

      {/* Placeholder grid — replaced in Sub-Task 6 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Profile
          </h2>
          <p className="mt-2 text-2xl font-bold">—</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Complete your assessment to build your profile
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Action Items
          </h2>
          <p className="mt-2 text-2xl font-bold">—</p>
          <p className="mt-1 text-sm text-muted-foreground">
            No active plans yet
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            AI Copilot
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Ready to assist — start a conversation
          </p>
        </div>
      </div>
    </div>
  );
}
