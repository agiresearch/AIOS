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

  // Ex


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (content: string, attachments: File[]) => {
    if (content.trim() || attachments.length > 0) {
      const newMessage: Message = {
        id: generateSixDigitId(),
        text: content,
        sender: 'user',
        timestamp: new Date(),
        attachments: attachments.map(file => file.name),
        thinking: false
      };
      setMessages([...messages, newMessage]);

      const messageId = generateSixDigitId();

      // Handle file uploads here (e.g., to a server)
      const botMessage: Message = {
        id: messageId,
        text: ``,
        sender: 'bot',
        timestamp: new Date(),
        thinking: true
      };

      setMessages(prevMessages => [...prevMessages, botMessage]);

      const res = await _(parseNamedContent(parseText(content))[0] as AgentCommand)

      setMessages(prevMessages => [...prevMessages].map(message => {
        if (message.id == messageId) {
          return { ...message, thinking: false, text: res.content };
        }
        // return res.content;
        return message;
      }));
    }

  };

  const addChat = () => {
    const newChat: Chat = { id: Date.now(), name: `Chat ${chats.length + 1}` };
    setChats([...chats, newChat]);
    setActiveChat(newChat.id);
  };

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
