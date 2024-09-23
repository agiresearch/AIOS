import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
    const { searchParams } = new URL(request.url);
    const name = searchParams.get('name');

    if (name) {
        const result = await prisma.agent.findFirst({
            where: {
                name,
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