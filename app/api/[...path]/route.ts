import { NextRequest } from 'next/server'

const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080'

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
  const path = pathSegments.join('/')
  const targetUrl = `${backendUrl}/api/${path}${request.nextUrl.search}`

  const headers = new Headers()
  const contentType = request.headers.get('content-type')
  if (contentType) {
    headers.set('content-type', contentType)
  }

  const init: RequestInit = {
    method: request.method,
    headers,
  }

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.arrayBuffer()
  }

  const response = await fetch(targetUrl, init)

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  })
}

type RouteContext = { params: { path: string[] } }

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context.params.path)
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context.params.path)
}

export async function HEAD(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context.params.path)
}
