import { NextResponse } from "next/server";

/**
 * Clerk webhook BFF proxy.
 * Clerk sends webhooks to this Next.js route, which forwards them
 * to the FastAPI backend to avoid CORS issues with the browser.
 *
 * Configure Clerk to POST to: https://your-app.vercel.app/api/webhooks/clerk
 */
export async function POST(request: Request) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  const body = await request.text();
  const headers = new Headers(request.headers);

  const response = await fetch(`${apiUrl}/api/v1/auth/webhook`, {
    method: "POST",
    headers,
    body,
  });

  return new NextResponse(await response.text(), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
