export const dynamic = 'force-dynamic'

import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
  
    const result  = await prisma.agent.findMany();
    
    return NextResponse.json({status : 'success', ...result});
  }