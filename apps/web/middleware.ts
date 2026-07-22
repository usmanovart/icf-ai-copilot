import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/v1/auth/webhook",
]);

const isCoachRoute = createRouteMatcher(["/coach(.*)"]);
const isOrgAdminRoute = createRouteMatcher(["/workspace(.*)", "/members(.*)"]);

export default clerkMiddleware(async (auth, req) => {
  const { userId, orgRole } = await auth();

  // Redirect unauthenticated users trying to access protected routes
  if (!userId && !isPublicRoute(req)) {
    return NextResponse.redirect(new URL("/sign-in", req.url));
  }

  // Role-based access: coach routes
  if (
    isCoachRoute(req) &&
    orgRole !== "org:coach" &&
    orgRole !== "org:admin"
  ) {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  // Role-based access: org admin routes
  if (isOrgAdminRoute(req) && orgRole !== "org:admin") {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
};
