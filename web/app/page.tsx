"use client";

import Image from 'next/image'
import { IdeaCard } from '@/components/agents/IdeaCard';
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

    useEffect(() => {
        const _ = async () => {
            const response = await axios.get('http://localhost:8000/get_all_agents');
            setAgents(response.data.agents)
        }
        
        _()
    }, [])

    useAutosizeTextArea(textAreaRef.current, value);

    const handleQuery = () => {
        if (!chatStarted)
            setChatStarted(true);

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

    return (
        <main className="w-full h-screen overflow-hidden flex flex-row">
            <div className="h-full w-1/6"></div>
            <div className="h-full w-5/6 bg-white relative">
                {!chatStarted ? (<div className='center-panel flex flex-col w-2/3 absolute top-[40%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 items-center justify-center gap-y-8'>
                    <Image src={'https://avatars.githubusercontent.com/u/130198651?v=4'} width={460} height={460} alt={'AGI Research Logo'} className='w-[10%] aspect-square rounded-full' />
                    <div className='flex flex-row justify-between w-full gap-x-3 pt-4'>
                        <IdeaCard />
                        <IdeaCard />
                        <IdeaCard />
                        <IdeaCard />
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
                    <Button isIconOnly className='bg-transparent hover:opacity-40' onClick={() => handleQuery()}>
                        <SearchCode />
                    </Button>

                </div>
            </div>
        </main>
    );
}



