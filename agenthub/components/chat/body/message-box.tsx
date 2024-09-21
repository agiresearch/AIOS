import { Avatar, AvatarFallback, AvatarImage } from "@/components/chat/ui/avatar";
import Markdown from "./markdown";

interface MessageBoxProps {
    message: any
    userImageUrl?: string;
}

export const MessageBox = ({
    message,
    userImageUrl
}: MessageBoxProps) => {
    const nameString = message.role === "user" ? "You" : "TalkGPT";
    const imageUrl = message.role === "user" ? userImageUrl : "/logo.svg";

    return (
        <div
            className="flex space-x-3 items-start mb-10 max-w-[calc(80%)] md:max-w-full text-wrap"
        >
            <Avatar className="w-7 h-7 text-white fill-white">
                <AvatarImage src={imageUrl} className="text-white fill-white" />
                <AvatarFallback className="text-neutral-900 font-semibold">
                    {nameString[0]}
                </AvatarFallback>
            </Avatar>
            <div className="max-w-[calc(80%)]">
                <h3 className="font-bold">{nameString}</h3>
                <div className="flex flex-grow flex-col gap-3 gap-y-5">
                    <Markdown content={message.content} />
                </div>
            </div>
        </div>
    )
}