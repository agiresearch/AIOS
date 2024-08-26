import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function POST(request: Request): Promise<NextResponse> {
    if (request.body) {
        const body = await request.json();
        
        const result = await prisma.agentConfig.create({
            data: body
        })
    
        return NextResponse.json(result);
      } else {
        return NextResponse.json({status : 'fail'});
      }
}
