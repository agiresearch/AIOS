"use client";

import Image from 'next/image'
import { Example, IdeaCard } from '@/components/agents/IdeaCard';
import { useEffect, useRef, useState } from 'react';
import useAutosizeTextArea from '@/hooks/useAutosizeTextArea';
import { Textarea, Button } from '@nextui-org/react';
import { SearchCode } from 'lucide-react';

import { Mention, MentionsInput } from 'react-mentions'

import defaultStyle from '../components/agents/defaultStyle'
import defaultMentionStyle from '../components/agents/defaultMentionStyle';

import '../components/agents/s.css'
import Container from '@/components/agents/Container';
import { AgentCommand, ChatBreak, ChatBreakProps, ChatMessage, ChatMessageProps, isChatBreakProps, isChatMessageProps } from '@/components/agents/ChatMessage';
import axios from 'axios';

import { serverUrl } from '@/lib/env';

function parseAgentCommands(input: string): AgentCommand[] {
    const result: AgentCommand[] = [];
    const regex = /@\[([^\]]+)\]\(([^)]+)\)\s*([^@]*)/g;
    let match;

    while ((match = regex.exec(input)) !== null) {
        const [_, fullName, name, content] = match;
        result.push({
            name: name.trim(),
            content: content.trim()
        });
    }
    console.log('results', result)
    return result;
}

export default function AgentsPage() {
    const [value, setValue] = useState('');
    const textAreaRef = useRef<HTMLTextAreaElement>(null);
    const [chatStarted, setChatStarted] = useState(false);
    const [agents, setAgents] = useState<any>();
    const target = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        const _ = async () => {
            const response = await axios.get(`${serverUrl}/get_all_agents`);
            setAgents(response.data.agents)
        }

        _()
    }, [])

    const handleKeyDown = (event: any) => {
        if (event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.altKey) {
            event.preventDefault();
            //   console.log('Enter key pressed without any modifiers');
            if (target.current) {
                target.current.click()
            }
        }
    };

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, []);

    useAutosizeTextArea(textAreaRef.current, value);

    const handleQuery = () => {
        if (!chatStarted)
            setChatStarted(true);

        console.log('value is', value);
        const parsed = parseAgentCommands(value);

        setMessages((prev) => {
            return [
                ...prev,
                {
                    direction: 'right',
                    agentName: 'user',
                    query: parsed
                },
                {
                    size: 10
                },
                ...parsed.map(p => ({
                    direction: 'left',
                    agentName: p.name,
                    query: p.content
                } as ChatMessageProps)),

                {
                    size: 10
                },
            ]

        })

        setValue('')


    }

    const [messages, setMessages] = useState<Array<ChatMessageProps | ChatBreakProps>>([]);

    const callback = (a: Example[], phrase: string) => {
        if (!chatStarted)
            setChatStarted(true);

        console.log('value is', phrase);
        const parsed = parseAgentCommands(phrase);

        setMessages((prev) => {
            return [
                ...prev,
                {
                    direction: 'right',
                    agentName: 'user',
                    query: parsed
                },
                {
                    size: 10
                },
                ...parsed.map(p => ({
                    direction: 'left',
                    agentName: p.name,
                    query: p.content
                } as ChatMessageProps)),

                {
                    size: 10
                },
            ]

        })
    }

    // useEffect(() => {
    //     if (value.at(0) == ';' && value.at(1) == ';') {

    //     }
    // }, [value])

    return (
        <main className="w-full h-screen overflow-hidden flex flex-row">
            <div className="h-full w-1/6 flex flex-col items-center justify-center">
                <p className='text-3xl text-red-600'>Coming</p>
                <p className='text-3xl text-red-600'>Soon</p>
            </div>
            <div className="h-full w-5/6 bg-white relative">
                {!chatStarted ? (<div className='center-panel flex flex-col w-2/3 absolute top-[40%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 items-center justify-center gap-y-8'>
                    <Image src={'https://avatars.githubusercontent.com/u/130198651?v=4'} width={460} height={460} alt={'AGI Research Logo'} className='w-[10%] aspect-square rounded-full' />
                    <div className='flex flex-row justify-between w-full gap-x-3 pt-4'>
                        <IdeaCard examples={[
                            {
                                agent_name: 'example/math_agent',
                                task: 'What\'s 90+4?'
                            }
                        ]} cb={callback} phrase={`
                        @[Math Agent](example/math_agent) What's 90+4?
                        `} />
                        <IdeaCard examples={[
                            {
                                agent_name: 'example/academic_agent',
                                task: 'Get me information on sea turtles.'
                            }
                        ]} cb={callback} phrase={`
                        @[Academic Agent](example/academic_agent) Get me information on sea turtles.
                        `} />
                        <IdeaCard examples={[
                            {
                                agent_name: 'example/math_agent',
                                task: 'what is 45*2-4 to the power of 4'
                            },
                            {
                                agent_name: 'example/academic_agent',
                                task: 'What are the effects of smoking on cancer?'
                            }
                        ]} cb={callback} phrase={`
                        @[Math Agent](example/math_agent) what is 45*2-4 to the power of 4
                        @[Academic Agent](example/academic_agent) What are the effects of smoking on cancer?
                        `} />
                    </div>
                </div>) : (<div className='flex flex-col gap-y-3 pt-3'>
                    <div className='flex items-center flex-row gap-x-10 p-5 justify-center'>
                        <Image src={'https://avatars.githubusercontent.com/u/130198651?v=4'} width={460} height={460} alt={'AGI Research Logo'} className='w-[3%] aspect-square rounded-full' />
                        <p className='font-semibol text-3xl'>OpenAGI</p>
                    </div>
                    <Container>
                        {messages.map((message, index) => {
                            if (isChatBreakProps(message))
                                return <ChatBreak key={index} {...message} />
                            else if (isChatMessageProps(message))
                                return <ChatMessage key={index} {...message} />
                        })}
                    </Container>
                </div>)}
                <div className='input-panel flex w-2/3 absolute left-0 right-0 mx-auto bottom-[20px] bg-[#F4F4F4] h-fit overflow-visible outline-none flex-row p-4 rounded-2xl gap-x-4 items-center'>
                    <MentionsInput
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        style={defaultStyle}
                        className={'mention_input'}
                        placeholder={"Mention people using '@'"}
                        a11ySuggestionsListLabel={"Suggested mentions"}
                        allowSuggestionsAboveCursor={true}
                        customSuggestionsContainer={(children) => <div><span style={{ fontWeight: "bold" }}><h2>This container has customised suggestions</h2></span>{children}</div>}
                    >
                        <Mention data={agents} onAdd={undefined} style={defaultMentionStyle} trigger={'@'} />
                    </MentionsInput>
                    <Button isIconOnly className='bg-transparent hover:opacity-40' onClick={() => handleQuery()} ref={target}>
                        <SearchCode />
                    </Button>

                </div>
            </div>
        </main>
    );
}



