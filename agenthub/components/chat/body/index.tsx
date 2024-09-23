"use client";

import { ScrollArea } from "@/components/chat/ui/scroll-area";
import { useEffect, useRef, useState } from "react";
import { MessageBox } from "./message-box";

export interface BodyProps {
    messages: any[]
}

export const Body: React.FC<BodyProps> = ({
    messages,
}) => {
//     const messages = [
//         {
//         _id: '1',
//         role: 'assistant',
//         content: 'Hello from the assistant!',
//         imageUrl: 'data:image/png;base64,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'
//     },
//     {
//         _id: '2',
//         role: 'user',
//         content: 'Hi\n' + 'what is up\n'+'```python\n'+'print("hello world")\n'+'```\n\n'+"Bye!",
//         imageUrl: 'data:image/png;base64,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'
//     },
// ];

    const [displayedMessages, setDisplayedMessages] = useState<any[]>([]);

    useEffect(() => {
        console.log(messages)
        setDisplayedMessages(messages.map((msg, index) => ({
            _id: `${index}`,
            ...msg,
            imageUrl: ''
        })))
    }, [messages])

    const scrollRef = useRef<HTMLDivElement>(null);
    const [showButton, setShowButton] = useState(false);

    useEffect(() => {
        scrollToBottom();
    }, [messages])

    const scrollToBottom = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "auto" });
        }
    };

    return (
        <>
            <ScrollArea
                className="max-h-[calc(100%-100px)] h-fit py-8 w-full flex-1 bg-neutral-900 rounded-2xl shadow-xl"
            >
                <div className="px-4 sm:px-12 md:px-52 2xl:px-[430px] relative">
                    {displayedMessages.map((message) => (
                        <MessageBox
                            key={message._id}
                            message={message}
                            userImageUrl={message.imageUrl}
                        />
                    ))}
                </div>
                <div ref={scrollRef} />
            </ScrollArea>
        </>
    );
};