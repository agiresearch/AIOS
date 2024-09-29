"use client";

import { Button } from "@/components/chat/ui/button"

import { PlusCircle, SquarePen } from "lucide-react"

export const NewChatButton = () => {
    return (
        <Button
            className="w-full flex justify-start items-center bg-inherit hover:bg-inherit p-0"
            onClick={() => console.log('clicked')}
        >
            <PlusCircle className="w-5 h-5" />
            <p className="font-semibold text-start ml-3">New Chat</p>
            <SquarePen className="w-4 h-4 ml-auto" />
        </Button>
    )
}