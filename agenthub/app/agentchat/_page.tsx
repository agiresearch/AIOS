'use client'

import React, { useState, useRef, useEffect } from 'react';
import { ChatEditor } from '@/components/chat/editor/Editor';
import { useMounted } from '@/lib/mounted';

import { TextInput, ActionIcon, Switch, useMantineTheme, Button, CopyButton, Loader } from '@mantine/core';
import { Send, Sun, Moon, Plus, Hash, MessageCircle, Clipboard, Check } from 'lucide-react';
import { SidebarProps, HeaderProps, MessageBubbleProps, MessageListProps, InputAreaProps, Message, Chat } from '@/interfaces/agentchat';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import rehypeRaw from 'rehype-raw';


const Sidebar: React.FC<SidebarProps> = ({ chats, activeChat, setActiveChat, addChat, darkMode }) => (
    <div className={`w-60 flex-shrink-0 ${darkMode ? 'bg-gray-800' : 'bg-gray-200'} p-4 flex flex-col`}>
        <Button
            fullWidth
            leftSection={<Plus size={18} />}
            onClick={addChat}
            className={`mb-4 ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-300 hover:bg-gray-400'}`}
        >
            Add Chat
        </Button>
        <div className="space-y-2 overflow-y-auto flex-grow">
            {chats.map((chat) => (
                <Button
                    key={chat.id}
                    fullWidth
                    variant={chat.id === activeChat ? 'filled' : 'subtle'}
                    onClick={() => setActiveChat(chat.id)}
                    leftSection={<MessageCircle size={18} />}
                    className={`justify-start ${chat.id === activeChat
                        ? (darkMode ? 'bg-gray-600' : 'bg-gray-400')
                        : (darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-300')
                        }`}
                >
                    {chat.name}
                </Button>
            ))}
        </div>
    </div>
);

const Header: React.FC<HeaderProps> = ({ darkMode, setDarkMode }) => {
    const theme = useMantineTheme();
    return (
        <div className={`flex justify-between items-center p-4 border-b ${darkMode ? 'bg-gray-800 text-white border-gray-700' : 'bg-gray-100 text-black border-gray-200'}`}>
            <div className="flex items-center space-x-3">
                <Hash size={24} className="text-gray-500" />
                <h1 className="text-xl font-semibold">General</h1>
            </div>
            <div className="flex items-center space-x-3">
                <Sun size={18} className={darkMode ? 'text-gray-400' : 'text-yellow-500'} />
                <Switch
                    checked={darkMode}
                    onChange={(event) => setDarkMode(event.currentTarget.checked)}
                    size="md"
                    color={theme.primaryColor}
                />
                <Moon size={18} className={darkMode ? 'text-blue-400' : 'text-gray-400'} />
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
    console.log(typeof content)
    console.log(content)
    return (
        <ReactMarkdown
            rehypePlugins={[rehypeRaw]}
            components={{
                code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match && (props as any).inline;
                    return isInline ? (
                        <code className={`${className} ${darkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded px-1 py-0.5`} {...props}>
                            {children}
                        </code>
                    ) : (
                        <div className="relative">
                            <div className="flex justify-between items-center px-4 py-2 bg-gray-800 rounded-t-md">
                                <span className="text-sm text-gray-400">{match ? match[1] : 'text'}</span>
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
            {content}
        </ReactMarkdown>
    );
};

// Updated MessageBubble component
const MessageBubble: React.FC<MessageBubbleProps> = ({ message, darkMode, index, isThinking = false }) => (
    <div
      className={`flex items-start space-x-3 py-2 px-6 ${
        darkMode ? 'hover:bg-gray-600/30' : 'hover:bg-gray-200/50'
      } transition-colors duration-200 animate-slideIn opacity-0`}
      style={{ animationDelay: `${index * 0.05}s`, animationFillMode: 'forwards' }}
    >
      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white flex-shrink-0 ${
        message.sender === 'user' ? 'bg-blue-500' : 'bg-green-500'
      }`}>
        {message.sender === 'user' ? 'U' : 'B'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline space-x-2">
          <span className={`font-semibold truncate ${darkMode ? 'text-white' : 'text-black'}`}>
            {message.sender === 'user' ? 'User' : 'Bot'}
          </span>
          <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <div className={`mt-1 break-words ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          {isThinking ? (
            <div className="flex items-center space-x-2 animate-pulse">
              <Loader size="sm" />
              <span>Agent is thinking...</span>
            </div>
          ) : (
            <Markdown content={message.text} darkMode={darkMode} />
          )}
        </div>
      </div>
    </div>
  );

  const MessageList: React.FC<MessageListProps> = ({ messages, darkMode }) => (
    <div className={`flex-grow overflow-y-auto ${darkMode ? 'bg-gray-700' : 'bg-white'}`}>
      <div className="py-4 space-y-1">
        {messages.map((message, index) => (
          <MessageBubble 
            key={message.id} 
            message={message} 
            darkMode={darkMode} 
            index={index}
            isThinking={message.sender === 'bot' && message.text === ''}
          />
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
          };
          setMessages([...messages, newMessage]);
      
          // Immediately add a "thinking" message for the bot
        //   const thinkingMessage: Message = {
        //     id: Date.now() + 1,
        //     text: '',
        //     sender: 'bot',
        //     timestamp: new Date(),
        //   };
        //   setMessages(prevMessages => [...prevMessages, thinkingMessage]);

          const noInterpolation = (strings: any, ...values: any) => strings.join('');
      
          // Simulate bot response after a delay
          setTimeout(() => {
            const botMessage: Message = {
              id: 1,
              text: noInterpolation`Here's a sample response with Markdown:
              
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
            };
            // setMessages(prevMessages => 
            //   prevMessages.map(msg => msg.id === thinkingMessage.id ? botMessage : msg)
            // );
            setMessages(prevMessages => [...prevMessages, botMessage]);
            
          }, 3000); // Increased delay to 3 seconds to make the loading state more noticeable
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
                darkMode={darkMode}
            />
            <div className="flex flex-col flex-grow">
                <Header darkMode={darkMode} setDarkMode={setDarkMode} />
                <MessageList messages={messages} darkMode={darkMode} />
                {mounted && <ChatEditor onSend={handleSend} darkMode={darkMode} />}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};


export default ChatInterface;