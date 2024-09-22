import { NextResponse } from 'next/server';
import prisma from '../../../lib/prisma'

export async function POST(request: Request): Promise<NextResponse> {
    if (request.body) {
        const body = await request.json();
        
        // Destructure the body to separate agent data from files
        const { author, name, version, license, files, ...otherData } = body;

        try {
            const result = await prisma.agent.create({
                data: {
                    author,
                    name,
                    version,
                    license,
                    ...otherData,
                    files: {
                        //@ts-ignore
                        create: files.map((file: any) => ({
                            path: file.path,
                            content: file.content
                        }))
                    }
                },
                include: {
                    files: true
                }
            });

            return NextResponse.json(result);
        } catch (error) {
            console.error('Error creating agent:', error);
            return NextResponse.json({ status: 'error', message: 'Failed to create agent' }, { status: 500 });
        }
    } else {
        return NextResponse.json({ status: 'fail', message: 'No body provided' }, { status: 400 });
    }
}