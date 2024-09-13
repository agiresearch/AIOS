import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
  const { searchParams } = new URL(request.url);
  const name = searchParams.get('name');
  const version = searchParams.get('version');
  const author = searchParams.get('author');

  if (name && version && author) {
    const result = await prisma.agent.findFirst({
      where: {
        name,
        version,
        author
      },
      include: {
        files: true
      }
    });

    if (result != null) {
      return NextResponse.json({ ...result });
    }
  } else if (name && author) {
    const result = await prisma.agent.findFirst({
      where: {
        name,
        author
      },
      include: {
        files: true
      }
    });

    if (result != null) {
      return NextResponse.json({ ...result });
    }

  }





  return NextResponse.json({ status: 'fail' });
}