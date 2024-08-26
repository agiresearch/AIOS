/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import { useEffect, useRef, useState } from "react";

import axios from 'axios';

import Container from "./container"

import { AgentCommand, ChatMessage, ChatMessageProps } from "./ChatMessage";
import { serverUrl } from '@/lib/env';

import defaultStyle from '@/components/agents/defaultStyle'
import defaultMentionStyle from '@/components/agents/defaultMentionStyle';
import { Mention, MentionsInput } from "react-mentions";

import '@/components/agents/s.css'
import { Example } from "../agents/IdeaCard";

interface InterfaceProps {
    // secureHandler: (request: (data: string, key: string) => Promise<void>, d: string) => Promise<void>
}

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

export const Interface: React.FC<InterfaceProps> = () => {
    const [agents, setAgents] = useState<any>();
    const target = useRef<HTMLButtonElement>(null);
    const [value, setValue] = useState('');

    const [chatStarted, setChatStarted] = useState(false);
    const [messages, setMessages] = useState<Array<ChatMessageProps>>([]);

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
                ...parsed.map(p => ({
                    direction: 'left',
                    agentName: p.name,
                    query: p.content
                } as ChatMessageProps)),
            ]

        })

        setValue('')
    }

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
                ...parsed.map(p => ({
                    direction: 'left',
                    agentName: p.name,
                    query: p.content
                } as ChatMessageProps)),

            ]

        })
    }


    return <div className='h-full w-[85%] bg-inherit flex flex-col  border-[rgba(153, 153, 153, 0.5)] border-r-1'>
        <Container >
            {messages.map((message, index) => {

                return <ChatMessage key={index} {...message} />
            })}
        </Container>
        <div className='h-[16%] w-full border-t-1 border-[rgba(153, 153, 153, 0.5)] flex flex-row-reverse items-center pr-8 gap-x-10'>
            <button onClick={() => handleQuery()}
                className="items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 bg-[#fff] hover:bg-slate-200 h-10 px-4 py-2 flex gap-3 text-[#1f1f1f]"><div>Submit</div><div className="hidden md:flex gap-1 font-xs opacity-50 items-center">Ctrl<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-plus "><path d="M5 12h14"></path><path d="M12 5v14"></path></svg><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-corner-down-left "><polyline points="9 10 4 15 9 20"></polyline><path d="M20 4v7a4 4 0 0 1-4 4H4"></path></svg></div></button>

            <div className='flex flex-1' />
            <div className='flex w-[16px]' />
            <div className='max-w-full max-h-[90%] h-fit w-full p-2 border-white rounded-2xl border-1'>

                <MentionsInput
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    style={defaultStyle}
                    className={'mention_input'}
                    placeholder={"Tag agents using '@'"}
                    a11ySuggestionsListLabel={"Suggested mentions"}
                    allowSuggestionsAboveCursor={true}
                    customSuggestionsContainer={(children) => <div><span style={{
                        fontWeight: 700, backgroundColor:
                            '#3c3937'
                    }}><h2 className='bg-inherit p-2 rounded-t-2xl'>Select an agent below</h2></span>{children}</div>}
                >
                    <Mention data={agents} onAdd={undefined} style={defaultMentionStyle} trigger={'@'} />
                </MentionsInput>
            </div>
            <div className='flex w-[16px]' />
        </div>
    </div>
}