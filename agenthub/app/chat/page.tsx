"use client";

import { Body } from "@/components/chat/body";
import { Form } from "@/components/chat/form";
import { Header } from "@/components/chat/header";
import "quill-mention/autoregister";

import { useMounted } from "@/lib/mounted";
import { useEffect, useState } from "react";

const Chat = () => {
    const [isMounted, setIsMounted] = useState(false)

    useEffect(() => {
        setIsMounted(true)
    }, [])

    return (
        isMounted ? <div className="bg-neutral-800 w-full h-[85vh] flex flex-col items-center">
            {/* <Header /> */}
            <div className='h-[40px] w-full'></div>
            <div className="flex flex-col h-full w-3/5 items-center relative">
                <Body />
                <div className="w-full fixed bottom-0">
                    <Form />
                    <p className="w-full text-center text-xs text-neutral-400 py-2 lg:pr-[300px] bg-neutral-800 ">TalkGPT could make errors. Consider checking important information.</p>
                </div>
            </div>
        </div> : null
    )
}

export default Chat;