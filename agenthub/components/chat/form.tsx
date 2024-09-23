"use client"

import { Input } from "@/components/chat/ui/input";
import { useState, useRef, useEffect, useMemo } from "react";
import axios from 'axios';
import { serverUrl } from "@/lib/env";
import { ChatMessageProps } from "./body/message-box";
import { useMounted } from "@/lib/mounted";
import dynamic from "next/dynamic";
import { Editor } from "./editor/Editor";

import { AgentCommand } from "./body/message-box";

export interface FormProps {
    callback: (s: any) => Promise<void>
}


export const Form: React.FC<FormProps> = ({
    callback
}) => {
    const [agents, setAgents] = useState<any[]>();
    const target = useRef<HTMLButtonElement>(null);
    const [value, setValue] = useState('');

    const [chatStarted, setChatStarted] = useState(false);
    const [messages, setMessages] = useState<Array<ChatMessageProps>>([]);
    const [mentionModule, setMentionModule] = useState<any>();

    const mounted = useMounted();

    // const [Editor, setEditor] = useState<any>();
    // const Editor = dynamic(() => import('./editor/Editor').then(mod => mod.Editor), { 
    //     ssr: false 
    //   })
    useEffect(() => {
        const checkForEditor = () => {
          const editorElement = document.querySelector('.editor');
          if (editorElement) {
            console.log('.editor element is now loaded and present');
            // Your code to run after .editor is loaded
            // For example, attaching event listeners:
            // editorElement.addEventListener('click', handleEditorClick);
            console.log(document.querySelector('.editor'))
          document.querySelector('.editor')!.addEventListener('keydown', handleKeyDown, true); // The 'true' here enables the capture phase
          editorElement.setAttribute('placeholder', 'Talk to AIOS')

          editorElement.addEventListener('focus', function() {
            //@ts-ignore
            const placeholder = this.getAttribute('placeholder');
             //@ts-ignore
            if (this.innerHTML.trim() === placeholder) {
                 //@ts-ignore
                this.innerHTML = '';
            }
        });

        editorElement.addEventListener('blur', function() {
             //@ts-ignore
            if (this.innerHTML.trim() === '') {
                 //@ts-ignore
                this.innerHTML = '';
            }
        });
          } else {
            // If .editor is not found, check again after a short delay
            setTimeout(checkForEditor, 100);
          }
        };
    
        // Start checking for the .editor element
        checkForEditor();
    
        // Cleanup function (if needed)
        return () => {
          // Remove any event listeners if you added any
        };
      }, []);


    useEffect(() => {
        const _ = async () => {
            const response = await axios.post('https://agenthub.aios.foundation/api/proxy', {
                type: 'GET',
                url: `${serverUrl}/get_all_agents`,
            });
            setAgents(response.data.agents)
        }
        _()

        if (window) {
            window.onload = function () {
                console.log(document.querySelector('.editor'))
                document.querySelector('.editor')!.addEventListener('keydown', handleKeyDown, true); // The 'true' here enables the capture phase
            }
        }
        

        // if (document)
        // document.querySelector('.editor')!.addEventListener('keydown', handleKeyDown, true); // The 'true' here enables the capture phase

        
        // setEditor(_editor);
    }, [])


    const [message, setMessage] = useState<string>("");

    const handleSendMessage = async (s: string) => {
        
        if (s=== "") return;
        const temp = s;

        
        document.querySelector('.editor')!.innerHTML = '';
        await callback(s)
        // await sendMessage({
        //     role: "user",
        //     content: temp,
        // });
    }

    const handleKeyDown = (e: any) => {
        if (e.key === "Enter") {
            e.stopImmediatePropagation();
            e.preventDefault();

            setMessage((prev) => {
                handleSendMessage(prev);
                return ''
            })

            
        }
    }

    const [isMounted, setIsMounted] = useState(false)
  
  useEffect(() => {
    setIsMounted(true)
  }, [])

    if (!isMounted) {
        return null // or a loading placeholder
    }

    const handleChange = (s: string) => {
        setMessage(s);
    }

    return (
        <div className="relative px-2 sm:px-12 md:px-52 2xl:px-96 w-3/5 mx-auto bg-neutral-800">
            {mounted && <Editor callback={handleChange} />}
            {/* <Input
                placeholder="Message TalkGPT..."
                className="border-[1px] border-neutral-500 ring-none rounded-xl bg-inherit text-neutral-200 placeholder:text-neutral-400 h-12"
                value={message}
                onChange={(e: any) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
            /> */}
            
        </div>
    );
};