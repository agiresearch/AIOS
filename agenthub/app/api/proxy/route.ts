// app/api/proxy/route.ts

import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

export async function POST(request: Request): Promise<NextResponse> {
  try {
    const { type, payload, url } = await request.json()

    if (!type || !url) {
      return NextResponse.json({ message: 'Missing required parameters' }, { status: 400 })
    }

    let response

    switch (type.toUpperCase()) {
      case 'GET':
        response = await axios.get(url)
        break
      case 'POST':
        response = await axios.post(url, payload)
        break
      case 'PUT':
        response = await axios.put(url, payload)
        break
      case 'DELETE':
        response = await axios.delete(url)
        break
      default:
        return NextResponse.json({ message: 'Unsupported request type' }, { status: 400 })
    }

    // Return the proxied response as-is
    return new NextResponse(JSON.stringify(response.data), {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Forward the error response if it's an Axios error
      if (error.response) {
        return new NextResponse(JSON.stringify(error.response.data), {
          status: error.response.status,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      } else {
        return NextResponse.json({ message: error.message }, { status: 500 })
      }
    } else {
      // For other types of errors
      return NextResponse.json({ message: 'An unexpected error occurred' }, { status: 500 })
    }
  }
}

// Optionally, you can add this to disallow other HTTP methods
export async function GET() {
  return NextResponse.json({ message: 'Method Not Allowed' }, { status: 405 })
}

export async function PUT() {
  return NextResponse.json({ message: 'Method Not Allowed' }, { status: 405 })
}

export async function DELETE() {
  return NextResponse.json({ message: 'Method Not Allowed' }, { status: 405 })
}