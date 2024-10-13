'use client'

import React, { useState, useRef, useEffect } from 'react';
import { ChatEditor } from '@/components/chat/editor/Editor';
import { useMounted } from '@/lib/mounted';

import { TextInput, ActionIcon, Switch, useMantineTheme, Button, CopyButton, Loader, Tooltip } from '@mantine/core';
import { Send, Sun, Moon, Plus, Hash, MessageCircle, Clipboard, Check, Lock, Edit2, X } from 'lucide-react';
import { SidebarProps, HeaderProps, MessageBubbleProps, MessageListProps, InputAreaProps, Message, Chat } from '@/interfaces/agentchat';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import rehypeRaw from 'rehype-raw';


const AgentLoader = () => {
    return <div className="flex items-center space-x-2 animate-pulse">
        <Loader size="sm" />
        <span>Agent is thinking...</span>
    </div>
}

const updateChatName = (chatId: number, newName: string) => {
    // setChats(prevChats => 
    //   prevChats.map(chat => 
    //     chat.id === chatId ? { ...chat, name: newName } : chat
    //   )
    // );
  };

const Sidebar: React.FC<SidebarProps> = ({ chats, activeChat, setActiveChat, addChat, updateChatName, darkMode }) => {
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editingName, setEditingName] = useState('');
  
    const categoryStyle = "text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2 mt-4 px-2 flex justify-between items-center";
    const channelStyle = `flex items-center justify-between rounded px-2 py-1.5 text-sm font-medium transition-colors duration-200 ease-in-out cursor-pointer`;
    const activeChannelStyle = darkMode ? 'bg-gray-700 text-white' : 'bg-gray-300 text-gray-900';
    const inactiveChannelStyle = darkMode ? 'text-gray-400 hover:bg-gray-700 hover:text-gray-200' : 'text-gray-700 hover:bg-gray-200 hover:text-gray-900';
  
    const startEditing = (chat: Chat) => {
      setEditingId(chat.id);
      setEditingName(chat.name);
    };
  
    const cancelEditing = () => {
      setEditingId(null);
      setEditingName('');
    };
  
    const saveEditing = () => {
      if (editingId !== null && editingName.trim() !== '') {
        updateChatName(editingId, editingName.trim());
        setEditingId(null);
      }
    };
  
    return (
      <div className={`w-60 flex-shrink-0 ${darkMode ? 'bg-gray-800' : 'bg-gray-100'} p-3 flex flex-col`}>
        <div className={`p-4 ${darkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded-lg mb-4`}>
          <h2 className={`font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Your Workspace</h2>
        </div>
        
        <div className="flex-grow overflow-y-auto">
          <div className={categoryStyle}>
            Channels
            <Tooltip label="Add Channel" position="right">
              <ActionIcon 
                onClick={addChat} 
                variant="subtle" 
                color={darkMode ? "gray" : "dark"}
                className="hover:bg-gray-600"
              >
                <Plus size={16} />
              </ActionIcon>
            </Tooltip>
          </div>
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={`${channelStyle} ${chat.id === activeChat ? activeChannelStyle : inactiveChannelStyle}`}
            >
              {editingId === chat.id ? (
                <div className="flex items-center w-full">
                  <Hash size={16} className="mr-2 flex-shrink-0" />
                  <TextInput
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    className="flex-grow"
                    size="xs"
                    autoFocus
                    onKeyPress={(e) => e.key === 'Enter' && saveEditing()}
                  />
                  <ActionIcon size="sm" onClick={saveEditing} className="ml-1">
                    <Check size={14} />
                  </ActionIcon>
                  <ActionIcon size="sm" onClick={cancelEditing} className="ml-1">
                    <X size={14} />
                  </ActionIcon>
                </div>
              ) : (
                <>
                  <div className="flex items-center flex-grow" onClick={() => setActiveChat(chat.id)}>
                    <Hash size={16} className="mr-2 flex-shrink-0" />
                    <span className="truncate">{chat.name}</span>
                  </div>
                  <Tooltip label="Rename Channel" position="right">
                    <ActionIcon 
                      onClick={() => startEditing(chat)} 
                      variant="subtle" 
                      color={darkMode ? "gray" : "dark"}
                      className="opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    >
                      <Edit2 size={14} />
                    </ActionIcon>
                  </Tooltip>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const Header: React.FC<HeaderProps> = ({ darkMode, setDarkMode }) => {
    const theme = useMantineTheme();
    return (
      <div className={`flex justify-between items-center p-3 border-b ${darkMode ? 'bg-gray-900 text-white border-gray-800' : 'bg-white text-black border-gray-200'}`}>
        <div className="flex items-center space-x-2">
          <Hash size={20} className="text-gray-500" />
          <h1 className="text-lg font-medium">General</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Sun size={16} className={darkMode ? 'text-gray-400' : 'text-yellow-500'} />
          <Switch
            checked={darkMode}
            onChange={(event) => setDarkMode(event.currentTarget.checked)}
            size="sm"
            color={theme.primaryColor}
          />
          <Moon size={16} className={darkMode ? 'text-blue-400' : 'text-gray-400'} />
        </div>
      </div>
    );
  };



// Improved Markdown component
interface MarkdownProps {
    content: string;
    darkMode: boolean;
}

const Markdown: React.FC<MarkdownProps> = ({ content, darkMode }) => {
    const [displayedText, setDisplayedText] = useState('');
    const animationRef = useRef<number | null>(null);
    const currentIndexRef = useRef(0);

    useEffect(() => {
        let lastTimestamp: number | null = null;
    
        const streamText = (timestamp: number) => {
            if (lastTimestamp === null) {
                lastTimestamp = timestamp;
            }
    
            const elapsed = timestamp - lastTimestamp;
    
            if (elapsed >= 30) { // Minimum 30ms between updates
                if (currentIndexRef.current < content.length) {
                    const chunkSize = Math.floor(Math.random() * 3) + 1;
                    const nextChunk = content.slice(currentIndexRef.current, currentIndexRef.current + chunkSize);
    
                    setDisplayedText(prevText => prevText + nextChunk);
                    currentIndexRef.current += chunkSize;
    
                    // Determine the next delay
                    let delay = Math.floor(Math.random() * 50) + 30;
    
                    if (nextChunk.includes('.') || nextChunk.includes('!') || nextChunk.includes('?')) {
                        delay += Math.floor(Math.random() * 300) + 200;
                    } else if (nextChunk.includes(',') || nextChunk.includes(';')) {
                        delay += Math.floor(Math.random() * 150) + 100;
                    }
    
                    if (nextChunk.length > 5) {
                        delay += nextChunk.length * 10;
                    }
    
                    lastTimestamp = timestamp + delay;
                }
            }
    
            animationRef.current = requestAnimationFrame(streamText);
        };
    
        animationRef.current = requestAnimationFrame(streamText);

        return () => {
            if (animationRef.current !== null) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [content]);


    return (
        <ReactMarkdown
            rehypePlugins={[rehypeRaw]}
            components={{
                code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match && (props as any).inline;
                    return isInline ? (
                        <code className={`${className} ${darkMode ? '!bg-gray-700' : '!bg-gray-200'} rounded px-1 py-0.5`} {...props}>
                            {children}
                        </code>
                    ) : (
                        <div className="relative">
                            <div className="flex justify-between items-center px-4 py-2 bg-gray-800 rounded-t-md">
                                <span className="text-sm !text-[#e06c75]">{match ? match[1] : 'text'}</span>
                                <CopyButton value={String(children).replace(/\n$/, '')}>
                                    {({ copied, copy }) => (
                                        <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
                                            {copied ? <Check size={16} /> : <Clipboard size={16} />}
                                        </ActionIcon>
                                    )}
                                </CopyButton>
                            </div>
                            <SyntaxHighlighter
                                language={match ? match[1] : 'text'}
                                style={atomDark as any}
                                PreTag="div"
                                className="rounded-b-md"
                            >
                                {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                        </div>
                    );
                },
                p: ({ children, ...props }) => <p className="mb-4 last:mb-0" {...props}>{children}</p>,
                br: ({ ...props }) => <br {...props} />,
                ul: ({ children }) => <ul className="list-disc pl-6 mb-4">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-6 mb-4">{children}</ol>,
                li: ({ children }) => <li className="mb-2">{children}</li>,
                h1: ({ children }) => <h1 className="text-2xl font-bold mb-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-bold mb-3">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-bold mb-2">{children}</h3>,
                blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4">{children}</blockquote>
                ),
            }}
        >
            {displayedText}
        </ReactMarkdown>
    );
};

// Updated MessageBubble component
const MessageBubble: React.FC<MessageBubbleProps> = ({ message, darkMode, index, isThinking = false }) => (
    <div
      className={`flex items-start space-x-3 py-3 px-4 ${darkMode ? 'hover:bg-gray-800/50' : 'hover:bg-gray-100/50'
        } transition-colors duration-200 animate-slideIn opacity-0`}
      style={{ animationDelay: `${index * 0.05}s`, animationFillMode: 'forwards' }}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0 ${message.sender === 'user' ? 'bg-blue-500' : 'bg-green-500'}`}>
        {message.sender === 'user' ? 'U' : 'B'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline space-x-2">
          <span className={`font-medium text-sm truncate ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
            {message.sender === 'user' ? 'User' : 'Bot'}
          </span>
          <span className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <div className={`mt-1 text-sm break-words ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          {isThinking ? <AgentLoader /> : <Markdown content={message.text} darkMode={darkMode} />}
        </div>
      </div>
    </div>
  );

  const MessageList: React.FC<MessageListProps> = ({ messages, darkMode }) => (
    <div className={`flex-grow overflow-y-auto ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="py-4 space-y-1">
        {messages.map((message, index) => (
          <MessageBubble key={message.id} message={message} darkMode={darkMode} index={index} isThinking={message.thinking} />
        ))}
      </div>
    </div>
  );

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
