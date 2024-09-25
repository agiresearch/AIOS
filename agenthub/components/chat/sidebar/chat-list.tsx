"use client";


import { useParams, useRouter } from "next/navigation";
import { ChatBox } from "./chat-box";
import { routeros } from "react-syntax-highlighter/dist/esm/styles/hljs";

export const ChatList = () => {
    const router = useRouter();
    const chats = [
        {
            _id: '1',
            title: 'Current'
        },
        {
            _id: '2',
            title: 'Sample'
        },
    ]

    return (
        <div className="flex flex-col flex-1 overflow-y-auto">
            {chats.map((chat) => (
                <ChatBox
                    key={chat._id}
                    chat={chat}
                    selected={chat._id === '1'}
                />
            ))}
        </div>
    )
}