import { cn } from "@/lib/utils";
import { ArrowDownToLine, Pencil, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface ChatBoxProps {
    chat: any;
    selected: boolean;
}

export const ChatBox = ({
    chat,
    selected
}: ChatBoxProps) => {

    const [isEditing, setIsEditing] = useState(false);
    const [title, setTitle] = useState(chat.title);

    const router = useRouter();

    const hadleClick = () => {
        if (!selected) {
            // router.push(`/chat/${chat._id}`);
            console.log(chat._id)
        }
    }

    const handleRename = () => {
        // rename({ id: chat._id, title: title });
        // setIsEditing(false);
    }

    const handleDelete = () => {
        // remove({ id: chat._id });
        // router.push("/");
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            // handleRename();
        }
    }

    return (
        <div key={chat.title} className={cn("group relative flex w-full p-2 rounded-md hover:bg-neutral-900 cursor-pointer text-white text-sm", selected && "bg-neutral-800")} onClick={hadleClick}>
            {isEditing ? (
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onBlur={handleRename}
                    autoFocus
                    className="outline-none bg-transparent w-[170px]"
                />
            ) : (
                <div className="truncate max-w-[200px]">{chat.title}</div>
            )}
            <div className="absolute top-1/2 -translate-y-1/2 right-2 flex z-10">
                {isEditing ? (
                    <button onClick={handleRename} className={cn("bg-gradient-to-r from-transparent from-0% to-neutral-900 to-30% pl-3 py-1", selected && "to-neutral-800")}>
                        <ArrowDownToLine />
                    </button>
                ) : (
                    <div className={cn("bg-gradient-to-r from-transparent from-0% to-neutral-900 to-30% space-x-2 flex pl-6 py-1", selected && "to-neutral-800")}>
                        <button onClick={() => setIsEditing(true)}>
                            <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={handleDelete}>
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>


        </div>
    )
}