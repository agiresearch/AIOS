"use client";

import { Body } from "@/components/chat/body";
import { Form } from "@/components/chat/form";
// import { Header } from "@/components/chat/header";

// import { useMounted } from "@/lib/mounted";
import { useEffect, useState } from "react";
import { baseUrl, serverUrl } from "@/lib/env";
import axios from 'axios';

import { AgentCommand } from "@/components/chat/body/message-box";

const Chat = () => {
    const [isMounted, setIsMounted] = useState(false)
    //@ts-ignore
    const [messages, setMessages] = useState<any[]>([]);

    useEffect(() => {
        setIsMounted(true)
    }, [])

    useEffect(() => {
        console.log('messages', messages)
    }, [messages])

    //@ts-ignore
    const addMessage = async (message: any) => { 
        // setMessages(prev => [...prev, ...parseAgentCommands(message)])
        setMessages(prev => [...prev, 
            {
                name: 'user',
                content: message == undefined ? 'No Agent Response' : message
            }])

        const promises = parseAgentCommands(message).map(command => _(command));
        const results = await Promise.all(promises);

        setMessages(prev => [...prev, ...results])
    }

    const _ = async (command: AgentCommand) => {
        const addAgentResponse = await axios.post(`${baseUrl}/api/proxy`, {
            type: 'POST',
            url: `${serverUrl}/add_agent`,
            payload: {
                agent_name: command.name,
                task_input: command.content,
            }
        });

        console.log(addAgentResponse.data);

        // Wait for 1050ms
        await new Promise(resolve => setTimeout(resolve, 1050));

        let recent_response: any;

        try {
             // Second request: Execute agent
            const executeAgentResponse = await axios.post(`${baseUrl}/api/proxy`, {
                type: 'GET',
                url: `${serverUrl}/execute_agent?pid=${addAgentResponse.data.pid}`,
            });

            console.log(executeAgentResponse.data);
            recent_response = executeAgentResponse.data.response.result.content;

            if (typeof recent_response !== 'string') {
                recent_response = "Agent Had Difficulty Thinking"
            }
        } catch (e) {
            recent_response = "Agent Had Difficulty Thinking"
        }
       

        //return recent_response
        return {
            name: command.name,
            content: recent_response
        };
    }

    function parseAgentCommands(input: string): AgentCommand[] {
        console.log('ji')
        const regex = /@([^\s]+)([^@]+)/g;
        const matches = input.matchAll(regex);
        const commands: AgentCommand[] = [];
    
        for (const match of matches) {
            const name = match[1].trim();
            const content = match[2].trim();
            if (name && content) {
                commands.push({ name: `${name}`, content });
            }
        }
        console.log(commands)
        return commands;
    }


    return (
        isMounted ? <div className="bg-neutral-800 w-full h-[85vh] flex flex-col items-center">
            {/* <Header /> */}
            <div className='h-[40px] w-full'></div>
            <div className="flex flex-col h-full w-3/5 items-center relative">
                <Body messages={messages} />
                <div className="w-full fixed bottom-0 bg-neutral-800">
                    <Form callback={addMessage} />
                    <p className="w-full text-center text-xs text-neutral-400 py-2 lg:pr-[300px ">AIOS could make errors. Consider checking important information.</p>
                </div>
            </div>
        </div> : null
    )
}

export default Chat;