export const dynamic = 'force-dynamic'

import { NextResponse } from 'next/server';
import prisma from '../../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
    //linter
    console.log(request)

    const result  = await prisma.agent.findMany({
        select: {
            id: true,
            author: true,
            name: true,
            version: true,
            description: true,
            createdAt: true
        }
    });
    
    return NextResponse.json({...result});
  }