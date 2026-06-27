import { NextRequest, NextResponse } from "next/server";

/**
 * Catch-all API proxy route.
 *
 * Proxies all /api/* requests from the frontend to the backend.
 * BACKEND_URL is read at request time (runtime env var) — not build time.
 * This allows changing the backend URL on Vercel without a code redeploy:
 *   1. Update BACKEND_URL in Vercel env vars dashboard
 *   2. Redeploy from cache (~1-2 min)
 *
 * Local development: set BACKEND_URL=http://127.0.0.1:8000 in frontend/.env
 * Production: set BACKEND_URL=https://your-backend.com in Vercel env vars
 */

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function getBackendUrl(): string {
  const url =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

async function proxy(request: NextRequest, path: string[]): Promise<NextResponse> {
  const backendUrl = getBackendUrl();
  const targetPath = "/" + path.join("/");
  const targetUrl = `${backendUrl}${targetPath}${request.nextUrl.search}`;

  // Forward the request body for POST/PUT/PATCH
  let body: BodyInit | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
  }

  // Build forward headers — strip host to avoid backend confusion
  const forwardHeaders = new Headers(request.headers);
  forwardHeaders.delete("host");

  try {
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      body,
      // @ts-expect-error Node.js fetch supports duplex
      duplex: "half",
    });

    // Build response headers — forward backend headers back to browser
    const responseHeaders = new Headers(backendResponse.headers);
    // Allow browser cross-origin access (tunnel URLs differ from vercel domain)
    responseHeaders.set("Access-Control-Allow-Origin", "*");
    responseHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    responseHeaders.set("Access-Control-Allow-Headers", "Content-Type, Authorization");

    return new NextResponse(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Proxy error";
    console.error(`[API Proxy] Failed to reach backend at ${targetUrl}:`, message);
    return NextResponse.json(
      {
        error: "Backend unreachable",
        detail: message,
        backend_url: backendUrl,
      },
      { status: 502 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxy(request, path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxy(request, path);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxy(request, path);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxy(request, path);
}

export async function OPTIONS(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}
