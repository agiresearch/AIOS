'use client'

import { Sidebar } from "@/components/modern/sidebar";
import { Settings } from '@/components/modern/settings'
import { Instruction } from "@/components/modern/instruction";
import { Interface } from "@/components/modern/interface";

import { useEffect, useState } from 'react';
import Image from 'next/image'

interface NightshadeProps {
    // keys: string[]
}

const Nightshade: React.FC<NightshadeProps> = () => {
    return <main className='bg-[#121418] text-[#f8f8f7] w-full overflow-hidden z-[60] relative flex flex-row' style={{
        height: 'calc(100vh)'
    }}>
        <Sidebar />
        <div className='w-[100vw] h-full bg-inherit flex flex-col'>
            <div className='h-[10%] w-full border-b-1 border-[rgba(153, 153, 153, 0.5)] flex flex-center items-center justify-start gap-x-5 px-3'>
                <div className="aspect-square h-4/5 rounded-full">
                    <Image src={'https://avatars.githubusercontent.com/u/130198651?v=4'} width={460} height={460} alt={'AGI Research Logo'} className='h-full w-full rounded-full' />
                </div>
                
                <h2 className="p-4 pl-[24px] text-2xl font-medium">AIOS</h2>
            </div>
            <div className='h-[90%] w-full flex flex-row'>
                <Instruction />
                <Interface />
                <Settings />
            </div>
        </div>
    </main>
}

export default Nightshade