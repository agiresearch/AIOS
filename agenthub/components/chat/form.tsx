"use client"

import { Input } from "@/components/chat/ui/input";
import { useState, useRef, useEffect, useMemo } from "react";
import axios from 'axios';
import { baseUrl, serverUrl } from "@/lib/env";
import { ChatMessageProps } from "./body/message-box";
import { useMounted } from "@/lib/mounted";
import dynamic from "next/dynamic";
import { Editor } from "./editor/Editor";

import { AgentCommand } from "./body/message-box";

export interface FormProps {
    callback: (s: any) => Promise<void>
}

function addPlaceholderToContentEditable(element: any, placeholderText: string) {
    // const element = document.getElementById(elementId);
    if (!element) return;

    // Create a span to hold the placeholder text
    const placeholder = document.createElement('span');
    placeholder.textContent = placeholderText;
    placeholder.style.color = '#999';
    placeholder.style.position = 'absolute';
    placeholder.style.pointerEvents = 'none';

    // Function to update placeholder visibility
    function updatePlaceholder() {
        const content = element!.textContent!.trim();
        console.log('content', content)
        if (content === '' && element!.children.length === 1 && element!.children[0].tagName === 'P') {
            if (!element!.contains(placeholder)) {
                element!.insertBefore(placeholder, element!.firstChild);
            }
        } else {
            console.log('else hit')
            if (element!.contains(placeholder)) {
                element!.removeChild(placeholder);
            }
        }
    }

    // Initial update
    updatePlaceholder();

    // Create a MutationObserver to watch for changes
    const observer = new MutationObserver(updatePlaceholder);

    // Configure the observer to watch for changes to childList and characterData
    observer.observe(element, {
        childList: true,
        characterData: true,
        subtree: true
    });

    // Add event listeners for focus and blur
    element.addEventListener('focus', function () {
        if (element!.textContent!.trim() === '') {
            element.innerHTML = '<p><br></p>';
            const range = document.createRange();
            const sel = window.getSelection();
            range.setStart(element!.firstChild!, 0);
            range.collapse(true);
            sel!.removeAllRanges();
            sel!.addRange(range);
        }
    });

    element.addEventListener('blur', updatePlaceholder);
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
                addPlaceholderToContentEditable(editorElement, 'Chat with AIOS')

            }



        }

        // Start checking for the .editor element
        checkForEditor();

        // Cleanup function (if needed)
        return () => {
            // Remove any event listeners if you added any
        };
    }, []);


    useEffect(() => {
        const _ = async () => {
            const response = await axios.post(`${baseUrl}/api/proxy`, {
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

        if (s === "") return;
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
        <div className="relative px-2 w-3/4 mx-auto bg-neutral-800">
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