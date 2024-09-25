import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function GET(request: Request): Promise<NextResponse> {
    const { searchParams } = new URL(request.url);
    const name = searchParams.get('name');
    const version = searchParams.get('version');

    console.log(name, version)

    if (name && version) {
        const result = await prisma.agent.findFirst({
            where: {
                name,
                version
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