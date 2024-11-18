'use client'

import React, { useState, useRef, useEffect } from 'react';
import { ChatEditor } from '@/components/chat/editor/Editor';
import { useMounted } from '@/lib/mounted';

import { Message, Chat } from '@/interfaces/agentchat';
import { Sidebar } from '@/components/agentchat/Sidebar';
import { Header } from '@/components/agentchat/Header';
import { MessageList } from '@/components/agentchat/MessageList';
import axios from 'axios';
import { AgentCommand } from '@/components/chat/body/message-box';
import { baseUrl, serverUrl } from '@/lib/env';
import { generateSixDigitId } from '@/lib/utils';

const ChatInterface: React.FC = () => {
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [chats, setChats] = useState<Chat[]>([
    { id: 1, name: 'General', messages: [] }
  ]);
  const [activeChat, setActiveChat] = useState<number>(1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  function parseText(input: string): string {
    // Step 1: Replace mention spans with the custom format
    let parsed = input.replace(/<span class="mention" data-type="mention" data-id="([^"]+)">@[^<]+<\/span>/g, '?>>$1/?>>');

    // Step 2: Convert <br> tags to newlines
    parsed = parsed.replace(/<br[^>]*>/g, '\n');

    // Step 3: Remove all remaining HTML tags
    parsed = parsed.replace(/<[^>]+>/g, '');

    // Decode HTML entities (e.g., &quot;, &amp;)
    parsed = parsed.replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'");

    return parsed.trim();
  }

  interface MessageBundle {
    name: string;
    content: string;
  }

  function parseNamedContent(inputString: string) {
    // Regular expression to match the pattern ?>>Name/?>>\s*Content
    const regex = /\?>>(.*?)\/?>>([^?]*)/g;
    const results = [];

    // Find all matches
    let match;
    while ((match = regex.exec(inputString)) !== null) {
      // Extract name and content, trim whitespace
      const name = match[1].trim().slice(0, -2);
      // Preserve newlines in content but trim surrounding whitespace
      const content = match[2].replace(/^\s+|\s+$/g, '');

      results.push({
        name,
        content
      });
    }

    return results;
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chats]);

  const handleSend = async (content: string, attachments: File[]) => {
    if (content.trim() || attachments.length > 0) {
      const newMessage: Message = {
        id: generateSixDigitId().toString(),
        text: content,
        sender: 'user',
        timestamp: new Date(),
        attachments: attachments.map(file => file.name),
        thinking: false
      };

      setChats(prevChats => prevChats.map(chat => 
        chat.id === activeChat
          ? { ...chat, messages: [...chat.messages, newMessage] }
          : chat
      ));

      const messageId = generateSixDigitId().toString();
      const botMessage: Message = {
        id: messageId,
        text: '',
        sender: 'bot',
        timestamp: new Date(),
        thinking: true
      };

      setChats(prevChats => prevChats.map(chat => 
        chat.id === activeChat
          ? { ...chat, messages: [...chat.messages, botMessage] }
          : chat
      ));

      const res = await processAgentCommand(parseNamedContent(parseText(content))[0] as AgentCommand);

      setChats(prevChats => prevChats.map(chat => 
        chat.id === activeChat
          ? {
              ...chat,
              messages: chat.messages.map(message => 
                message.id === messageId
                  ? { ...message, thinking: false, text: res.content }
                  : message
              )
            }
          : chat
      ));
    }
  };

  const addChat = () => {
    const newChat: Chat = {
      id: Date.now(),
      name: `Chat ${chats.length + 1}`,
      messages: []
    };
    setChats([...chats, newChat]);
    setActiveChat(newChat.id);
  };

  const processAgentCommand = async (command: AgentCommand) => {
    // Temporary measure to prevent hanging until draft is published
    if (!command) {
      return {
        name: undefined,
        content: "You must provide a mention to use AIOS. (@example/...)",
      }
    }

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

  const mounted = useMounted();

  const activeMessages = chats.find(chat => chat.id === activeChat)?.messages || [];

  // Add updateChatName function
  const updateChatName = (chatId: number, newName: string) => {
    setChats(prevChats => 
      prevChats.map(chat => 
        chat.id === chatId ? { ...chat, name: newName } : chat
      )
    );
  };

  // Add deleteChat function
  const deleteChat = (chatId: number) => {
    setChats(prevChats => {
      const filteredChats = prevChats.filter(chat => chat.id !== chatId);
      // If the deleted chat is the active one, switch to the first chat
      if (chatId === activeChat && filteredChats.length > 0) {
        setActiveChat(filteredChats[0].id);
      }
      return filteredChats;
    });
  };

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <Sidebar
        chats={chats}
        activeChat={activeChat}
        setActiveChat={setActiveChat}
        addChat={addChat}
        updateChatName={updateChatName}
        deleteChat={deleteChat}
        darkMode={darkMode}
      />
      <div className="flex flex-col flex-grow pb-4">
        <Header 
          darkMode={darkMode} 
          setDarkMode={setDarkMode}
          title={chats.find(chat => chat.id === activeChat)?.name || 'Chat'} 
        />
        <MessageList messages={activeMessages} darkMode={darkMode} />
        <div className='w-full flex h-fit justify-center'>
          {mounted && <ChatEditor onSend={handleSend} darkMode={darkMode} />}
        </div>

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatInterface;
