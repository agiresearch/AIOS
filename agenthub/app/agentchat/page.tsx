'use client'

import React, { useState, useRef, useEffect } from 'react';
import { ChatEditor } from '@/components/chat/editor/Editor';
import { useMounted } from '@/lib/mounted';

import { Message, Chat } from '@/interfaces/agentchat';
import { Sidebar } from '@/components/agentchat/Sidebar';
import { Header } from '@/components/agentchat/Header';
import { MessageList } from '@/components/agentchat/MessageList';




const updateChatName = (chatId: number, newName: string) => {
    // setChats(prevChats => 
    //   prevChats.map(chat => 
    //     chat.id === chatId ? { ...chat, name: newName } : chat
    //   )
    // );
  };


  



  

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [darkMode, setDarkMode] = useState<boolean>(false);
    const [chats, setChats] = useState<Chat[]>([{ id: 1, name: 'General' }]);
    const [activeChat, setActiveChat] = useState<number>(1);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, [messages]);

    const handleSend = (content: string, attachments: File[]) => {
        if (content.trim() || attachments.length > 0) {
            const newMessage: Message = {
                id: Date.now(),
                text: content,
                sender: 'user',
                timestamp: new Date(),
                attachments: attachments.map(file => file.name),
                thinking: false
            };
            setMessages([...messages, newMessage]);

            // Handle file uploads here (e.g., to a server)
            const botMessage: Message = {
                id: 3,
                text: `Here's a sample response with Markdown:

# Heading 1
## Heading 2

- List item 1
- List item 2

\`\`\`python
def greet(name):
  print(f"Hello, {name}!")

greet("World")
\`\`\`

> This is a blockquote.

**Bold text** and *italic text*.`,
                sender: 'bot',
                timestamp: new Date(),
                thinking: true
            };
            setMessages(prevMessages => [...prevMessages, botMessage]);

            setTimeout(() => {
                setMessages(prevMessages => [...prevMessages].map(message => {
                    if (message.id == 3) {
                        return { ...message, thinking: false };
                    }
                    return message;
                }));
            }, 3000);
        }
    };

    const addChat = () => {
        const newChat: Chat = { id: Date.now(), name: `Chat ${chats.length + 1}` };
        setChats([...chats, newChat]);
        setActiveChat(newChat.id);
    };

    const mounted = useMounted();

    return (
        <div className={`flex h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
          <Sidebar
            chats={chats}
            activeChat={activeChat}
            setActiveChat={setActiveChat}
            addChat={addChat}
            updateChatName={updateChatName}
            darkMode={darkMode}
        />
          <div className="flex flex-col flex-grow pb-4">
            <Header darkMode={darkMode} setDarkMode={setDarkMode} />
            <MessageList messages={messages} darkMode={darkMode} />
            <div className='w-full flex h-fit justify-center'>
                {mounted && <ChatEditor onSend={handleSend} darkMode={darkMode} />}
            </div>
            
            <div ref={messagesEndRef} />
          </div>
        </div>
      );
};


export default ChatInterface;
