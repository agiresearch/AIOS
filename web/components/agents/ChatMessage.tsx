import { FC, useEffect, useState } from "react";
import axios from 'axios';
import { Card, CardBody, Chip } from "@nextui-org/react";
// import { AgentMapping } from "@/exports";

import { Calculator, User, User2 } from "lucide-react";
import { TypeAnimation } from 'react-type-animation';
import type { } from 'ldrs'
 
import { StoryAgent, MathAgent } from '@/agents/build';

// export const agents = [
//     {
//         id: 'math',
//         display: 'Math Agent'
//     },
//     {
//         id: 'story',
//         display: 'Story Agent'
//     },
// ]


export interface AgentCommand {
    name: string;
    content: string;
}


//testing purposes
// async function delayedString(str: string): Promise<string> {
//     return new Promise((resolve) => {
//         setTimeout(() => {
//             resolve(str);
//         }, 6000);
//     });
// }



// const _ = async (s: string) => {
//     const r = await delayedString(s);
//     return r;
// }

export interface ChatMessageProps {
    direction: 'right' | 'left';
    agentName: 'math' | 'story' | 'user';
    query: string | AgentCommand[];
}

export interface ChatBreakProps {
    size: number
}

export const ChatBreak: FC<ChatBreakProps> = ({
    size
}) => {
    return <div className={`w-full h-[${size}px]`} />
}

export function isChatMessageProps(item: ChatBreakProps | ChatMessageProps): item is ChatMessageProps {
    return 'direction' in item && 'agentName' in item && 'query' in item;
}

export function isChatBreakProps(item: ChatBreakProps | ChatMessageProps): item is ChatBreakProps {
    return 'size' in item;
}

export const ChatMessage: FC<ChatMessageProps> = ({
    direction,
    agentName,
    query
}) => {
    const [response, setResponse] = useState('');

    // useEffect(() => {
    //     const _ = async (s: string, v: string) => {
    //         console.log(s, v)
    //         let q = '';
    //         if (v == 'story') {
    //             q = await StoryAgent(s);
    //         } else if (v == 'math') {
    //             q = await MathAgent(s);
    //             q = `The answer to the problem is ${q}`
    //         }

    //         setResponse(`${q}`);
    //     }

    //     if (agentName != 'user')
    //         _(query as string, agentName)
    // }, [])

    useEffect(() => {
        const _ = async (s: string, v: string) => {
            const _submit = await axios.post('http://localhost:8000/add_agent', {
                agent_name: v,
                task_input: s    
            });

            console.log(_submit.data)

            await new Promise(resolve => setTimeout(resolve, 1050));

            const response = await axios.get('http://localhost:8000/execute_agents')

            const recent_response = response.data.response[response.data.response.length-1].result.content
            setResponse(recent_response)
        }

        if (agentName != 'user')
            _(query as string, agentName)

    }, [])

    // const getAgentProperNameByKey = (key: string) => {
    //     for (const x of agents) {
    //         if (x.id == key) {
    //             return x.display
    //         }
    //     }
    // }


    return <div className={`px-0 w-full flex justify-start flex-row${direction == 'left' ? '' : '-reverse'} h-fit py-0`}>
        <Card className='w-[41%] h-full p-2 py-4'>
            {agentName != 'user' && <CardBody className='p-2 flex flex-col gap-y-2'>
                <div className='flex flex-row gap-x-3 items-center'>
                    {/* {AgentMapping[agentName].icon} */}
                    <Calculator color={'green'} />

                    {/* <p className='text-2xl font-semibold'>{AgentMapping[agentName].displayName}</p> */}
                    <p className='text-2xl font-semibold'>{agentName}</p>
                </div>
                <div className='flex items-center justify-center' style={{
                    alignItems: response == '' ? 'center' : 'center',
                    justifyContent: response == '' ? 'center' : 'start',
                }}>

                    {response != '' ? <TypeAnimation
                        sequence={[response]}
                        wrapper="span"
                        speed={50}
                        style={{ fontSize: '1.125rem', lineHeight: '1.75rem', display: 'inline-block' }}
                        repeat={0}
                        cursor={false}
                    /> :
                        <l-hatch
                            size="28"
                            stroke="4"
                            speed="3.5"
                            // color={AgentMapping[agentName].color}
                            color={'green'}
                        ></l-hatch>}
                </div>
            </CardBody>}
            {agentName == 'user' && <CardBody className='p-2 flex flex-col gap-y-2'>
                <div className='flex flex-row gap-x-3 items-center'>
                    <User2 color={'blue'} />
                    <p className='text-2xl font-semibold'>User</p>
                </div>
                <div className='text-base flex flex-col gap-y-2'>
                    {(query as AgentCommand[]).map((q, index) =>
                        <div className='flex flex-row gap-x-4' key={`sdgdsg-${index}`}>
                            {/* <Chip color={q.name == 'story' ? 'danger' : 'success'}>{getAgentProperNameByKey(q.name)}</Chip> */}
                            <Chip color={q.name == 'story' ? 'danger' : 'success'}>{q.name}</Chip>
                            <span>{q.content}</span>
                        </div>)}
                </div>
            </CardBody>}
        </Card>
    </div>
}