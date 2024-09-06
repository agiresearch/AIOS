import { FC, useEffect, useState } from "react";
import axios from 'axios';
import { Card, CardBody, Chip } from "@nextui-org/react";

import { Calculator, User, User2 } from "lucide-react";
import { TypeAnimation } from 'react-type-animation';
import type { } from 'ldrs'

import { serverUrl } from "@/lib/env";

export interface AgentCommand {
    name: string;
    content: string;
}


export interface ChatMessageProps {
    direction: 'right' | 'left';
    agentName: 'math' | 'story' | 'user';
    query: string | AgentCommand[];
}

export const ChatMessage: FC<ChatMessageProps> = ({
    direction,
    agentName,
    query
}) => {
    const [response, setResponse] = useState('');


    useEffect(() => {
        const _ = async (s: string, v: string) => {
            const _submit = await axios.post(`${serverUrl}/add_agent`, {
                agent_name: v,
                task_input: s    
            });

            console.log(_submit.data)

            await new Promise(resolve => setTimeout(resolve, 1050));

            const response = await axios.get(`${serverUrl}/execute_agent?pid=${_submit.data.pid}`)

            console.log(response.data)
            const recent_response = response.data.response.result.content
            
            setResponse(recent_response)
        }

        if (agentName != 'user')
            _(query as string, agentName)

    }, [])


    return <div className={`px-0 w-full flex justify-start flex-row h-fit py-0`}>
        <Card className='w-full h-full p-2 py-4 rounded-none bg-black border-1 border-white border-solid text-white'>
            {agentName != 'user' && <CardBody className='p-2 flex flex-col gap-y-2'>
                <div className='flex flex-row gap-x-3 items-center'>
                    <Calculator color={'green'} />

                    <p className='text-xl font-semibold text-white'>{agentName}</p>
                </div>
                <div className='flex items-center justify-center' style={{
                    alignItems: response == '' ? 'center' : 'center',
                    justifyContent: response == '' ? 'center' : 'start',
                }}>

                    {response != '' ? <TypeAnimation
                        sequence={[response]}
                        wrapper="span"
                        speed={50}
                        style={{ fontSize: '0.875rem', lineHeight: '1.25rem', display: 'inline-block', color: 'white' }}
                        repeat={0}
                        cursor={false}
                    /> :
                        <l-hatch
                            size="20"
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
                    <p className='text-xl font-semibold text-white'>User</p>
                </div>
                <div className='text-base flex flex-col gap-y-2'>
                    {(query as AgentCommand[]).map((q, index) =>
                        <div className='flex flex-row gap-x-4 items-center' key={`sdgdsg-${index}`}>
                            {/* <Chip color={q.name == 'story' ? 'danger' : 'success'}>{getAgentProperNameByKey(q.name)}</Chip> */}
                            <Chip color={q.name == 'story' ? 'danger' : 'success'} size={'sm'}>{q.name}</Chip>
                            <span className='text-sm text-white'>{q.content}</span>
                        </div>)}
                </div>
            </CardBody>}
        </Card>
    </div>
}