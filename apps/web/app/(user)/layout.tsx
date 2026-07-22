import { UserButton, OrganizationSwitcher } from "@clerk/nextjs";
import { SidebarNav } from "@/components/shared/SidebarNav";

/**
 * Layout for all user-facing protected routes (/dashboard, /assessment, /profile, etc.)
 * Renders the two-column shell: sidebar + main content area.
 */
export default function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="hidden w-64 flex-shrink-0 border-r border-border bg-background md:flex md:flex-col">
        <div className="flex h-16 items-center border-b border-border px-4">
          <span className="text-lg font-bold tracking-tight text-foreground">
            ICF AI Copilot
          </span>
        </div>
        <div className="flex-1 overflow-y-auto py-4">
          <SidebarNav />
        </div>
        <div className="border-t border-border p-4">
          <div className="flex items-center gap-3">
            <UserButton afterSignOutUrl="/sign-in" />
            <div className="min-w-0 flex-1">
              <OrganizationSwitcher
                hidePersonal={false}
                appearance={{
                  elements: {
                    rootBox: "w-full",
                    organizationSwitcherTrigger:
                      "w-full justify-start text-sm",
                  },
                }}
              />
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4 md:hidden">
          <span className="text-lg font-bold">ICF AI Copilot</span>
          <div className="flex items-center gap-2">
            <OrganizationSwitcher hidePersonal={false} />
            <UserButton afterSignOutUrl="/sign-in" />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
