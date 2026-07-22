"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ClipboardList,
  User,
  MessageSquare,
  CheckSquare,
  BarChart3,
  GitFork,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Assessment",
    href: "/assessment",
    icon: ClipboardList,
  },
  {
    label: "Profile",
    href: "/profile",
    icon: User,
  },
  {
    label: "AI Copilot",
    href: "/copilot",
    icon: MessageSquare,
  },
  {
    label: "Decision Twin",
    href: "/twin",
    icon: GitFork,
  },
  {
    label: "Action Plans",
    href: "/plans",
    icon: CheckSquare,
  },
  {
    label: "Insights",
    href: "/insights",
    icon: BarChart3,
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-1 px-2">
      {NAV_ITEMS.map((item) => {
        const isActive =
          pathname === item.href || pathname.startsWith(item.href + "/");
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
