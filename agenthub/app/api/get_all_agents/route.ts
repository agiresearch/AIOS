export const dynamic = 'force-dynamic'

import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
      //linter
      console.log(request)
      const result  = await prisma.agent.findMany();
    
    return NextResponse.json({...result});
  }