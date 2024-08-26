import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
    const { searchParams } = new URL(request.url);
    const name = searchParams.get('name');
    const version = searchParams.get('version');
  
    if (name) {
      const result  = await prisma.agentConfig.findFirst({where: { 
            name: name,
        }});
  
      if (result != null) {
        return NextResponse.json({status : 'success', ...result});
      }
    }
  
    return NextResponse.json({status : 'fail'});
  }