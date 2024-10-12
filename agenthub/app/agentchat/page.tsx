'use client'

import React, { useState, useRef, useEffect } from 'react';
import { TextInput, ActionIcon, Switch, useMantineTheme, Button } from '@mantine/core';
import { Send, Sun, Moon, Plus, Hash, MessageCircle } from 'lucide-react';

interface Message {
    id: number;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
}

interface HeaderProps {
    darkMode: boolean;
    setDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
}

interface MessageBubbleProps {
    message: Message;
    darkMode: boolean;
    index: number;
}

interface MessageListProps {
    messages: Message[];
    darkMode: boolean;
}

interface InputAreaProps {
    input: string;
    setInput: React.Dispatch<React.SetStateAction<string>>;
    handleSend: () => void;
    darkMode: boolean;
}


interface Chat {
    id: number;
    name: string;
}

interface SidebarProps {
    chats: Chat[];
    activeChat: number;
    setActiveChat: (id: number) => void;
    addChat: () => void;
    darkMode: boolean;
}

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

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, darkMode, index }) => (
    <div
        className={`flex items-start space-x-3 py-2 px-6 ${darkMode
                ? 'hover:bg-gray-600 hover:bg-opacity-30'
                : 'hover:bg-gray-200 hover:bg-opacity-50'
            } transition-colors duration-200 animate-slideIn opacity-0`}
        style={{ animationDelay: `${index * 0.05}s`, animationFillMode: 'forwards' }}
    >
        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white flex-shrink-0 ${message.sender === 'user' ? 'bg-blue-500' : 'bg-green-500'}`}>
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
            <p className={`mt-1 break-words ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{message.text}</p>
        </div>
    </div>
);

const MessageList: React.FC<MessageListProps> = ({ messages, darkMode }) => (
    <div className={`flex-grow overflow-y-auto ${darkMode ? 'bg-gray-700' : 'bg-white'}`}>
        <div className="py-4 space-y-1">
            {messages.map((message, index) => (
                <MessageBubble key={message.id} message={message} darkMode={darkMode} index={index} />
            ))}
        </div>
    </div>
);

const InputArea: React.FC<InputAreaProps> = ({ input, setInput, handleSend, darkMode }) => {
    const theme = useMantineTheme();
    return (
        <div className={`p-4 ${darkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
            <div className="flex space-x-3 items-center">
                <ActionIcon
                    variant="subtle"
                    color={darkMode ? 'gray' : 'dark'}
                    className="hover:bg-opacity-10 hover:bg-gray-400 transition-colors"
                >
                    <Plus size={20} />
                </ActionIcon>
                <TextInput
                    placeholder="Type a message..."
                    value={input}
                    onChange={(event) => setInput(event.currentTarget.value)}
                    onKeyPress={(event) => event.key === 'Enter' && handleSend()}
                    className="flex-grow"
                    styles={(theme) => ({
                        input: {
                            backgroundColor: darkMode ? theme.colors.gray[7] : theme.white,
                            color: darkMode ? theme.white : theme.black,
                            border: 'none',
                            borderRadius: '9999px',
                            padding: '10px 16px',
                            '&::placeholder': {
                                color: darkMode ? theme.colors.gray[5] : theme.colors.gray[6],
                            },
                        },
                        rightSection: {
                            width: '40px',
                        },
                    })}
                    rightSection={
                        <ActionIcon
                            onClick={handleSend}
                            variant="filled"
                            color={theme.primaryColor}
                            className="transition-colors"
                            radius="xl"
                            size="lg"
                        >
                            <Send size={18} />
                        </ActionIcon>
                    }
                    rightSectionWidth={40}
                />
            </div>
        </div>
    );
};

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState<string>('');
    const [darkMode, setDarkMode] = useState<boolean>(false);
    const [chats, setChats] = useState<Chat[]>([{ id: 1, name: 'General' }]);
    const [activeChat, setActiveChat] = useState<number>(1);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = () => {
        if (input.trim()) {
            const newMessage: Message = { id: Date.now(), text: input, sender: 'user', timestamp: new Date() };
            setMessages([...messages, newMessage]);
            setInput('');
            setTimeout(() => {
                const botMessage: Message = { id: Date.now(), text: 'This is a bot response.', sender: 'bot', timestamp: new Date() };
                setMessages(prevMessages => [...prevMessages, botMessage]);
            }, 1000);
        }
    };

    const addChat = () => {
        const newChat: Chat = { id: Date.now(), name: `Chat ${chats.length + 1}` };
        setChats([...chats, newChat]);
        setActiveChat(newChat.id);
    };

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
                <InputArea input={input} setInput={setInput} handleSend={handleSend} darkMode={darkMode} />
            </div>
        </div>
    );
};

export default ChatInterface;