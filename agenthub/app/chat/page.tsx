"use client";

import { Body } from "@/components/chat/body";
import { Form } from "@/components/chat/form";
import { Header } from "@/components/chat/header";

const Chat = () => {
    return (
        <div className="bg-neutral-800 w-full h-full flex flex-col items-center">
            <Header />
            <div className="flex flex-col h-[85vh] w-full">
                <Body />
                <div className="w-full fixed bottom-0">
                    <Form />
                    <p className="w-full text-center text-xs text-neutral-400 my-2 lg:pr-[300px]">TalkGPT could make errors. Consider checking important information.</p>
                </div>
            </div>
        </div>
    )
}

export default Chat;