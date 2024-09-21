import { Input } from "@/components/chat/ui/input";
import { useState } from "react";


export const Form = () => {
    const sendMessage = (a: any) => console.log(a);

    const [message, setMessage] = useState<string>("");

    const handleSendMessage = async () => {
        if (message === "") return;
        console.log("message sent");
        const temp = message;
        setMessage("");
        await sendMessage({
            role: "user",
            content: temp,
        });
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleSendMessage();
        }
    }

    return (
        <div className="relative px-2 sm:px-12 md:px-52 lg:pr-[500px] 2xl:px-96 w-full bg-neutral-800">
            <Input
                placeholder="Message TalkGPT..."
                className="border-[1px] border-neutral-500 ring-none rounded-xl bg-inherit text-neutral-200 placeholder:text-neutral-400 h-12"
                value={message}
                onChange={(e: any) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
            />
        </div>
    );
};