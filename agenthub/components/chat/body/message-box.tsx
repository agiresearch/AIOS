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
    console.log('name', message.name)
    const nameString = message.name === "user" ? "You" : "AIOS";
    // const imageUrl = message.role === "user" ? userImageUrl : "";
    const imageUrl = message.name == 'user' 
            ? 'https://aiosfoundation.org/assets/images/team/default-2.jpeg'
            : 'https://chat.aios.foundation/_next/image?url=https%3A%2F%2Favatars.githubusercontent.com%2Fu%2F130198651%3Fv%3D4&w=1080&q=75'

    // const imageUrl = userImageUrl;

    return (
        <div
            className="flex space-x-3 items-start mb-10 max-w-[calc(80%)] md:max-w-full text-wrap"
        >
            <Avatar className="w-10 h-10 text-white fill-white">
                <AvatarImage src={imageUrl} className="text-white fill-white" />
                <AvatarFallback className="text-neutral-900 font-semibold">
                    {nameString[0]}
                </AvatarFallback>
            </Avatar>
            <div className="max-w-full w-full">
                <h3 className="font-bold text-white text-xl">{nameString}</h3>
                <div className="flex flex-grow flex-col gap-3 gap-y-5 text-white">
                    <Markdown content={message.content} />
                </div>
            </div>
        </div>
    )
}

export interface ChatMessageProps {
    agentName: 'math' | 'story' | 'user';
    query: string | AgentCommand[];
}

export interface AgentCommand {
    name: string;
    content: string;
}
