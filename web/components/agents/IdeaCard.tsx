import { Chip } from "@nextui-org/react";
import { FC } from "react";

export interface Example {
    agent_name: string;
    task: string;
}

export interface IdeaCardProps {
    examples: Example[];
    phrase: string;
    cb: (a: Example[], s: string) => void
}

export const IdeaCard: FC<IdeaCardProps> = ({
    examples,
    phrase,
    cb
}) => {
    return <div className="flex flex-col gap-y-5 items-center justify-center hover:cursor-pointer w-[30%] p-4 rounded-lg shadow-lg border-1 border-gray-500 border-solid hover:bg-slate-500 bg-slate-200 aspect-video" onClick={() => {
        cb(examples, phrase);
    }}>
        {
            examples.map((example, index) => {
                return <div className='w-full flex flex-row gap-x-3' key={index}> 
                    <Chip color={'danger'}>{example.agent_name}</Chip>
                    <p className='text-sm'>{example.task}</p>
                </div>
            })
        }
    </div>
}  