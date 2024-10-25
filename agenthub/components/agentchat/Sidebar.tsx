import React, { useState } from 'react';

import { TextInput, ActionIcon, Tooltip } from '@mantine/core';
import { Plus, Hash, Check, Edit2, X } from 'lucide-react';
import { Chat } from '@/interfaces/agentchat';


export interface SidebarProps {
    chats: Chat[];
    activeChat: number;
    setActiveChat: (id: number) => void;
    addChat: () => void;
    updateChatName: (chatId: number, newName: string) => void;
    darkMode: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ chats, activeChat, setActiveChat, addChat, updateChatName, darkMode }) => {
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
          <h2 className={`font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Your AIOS Workspace</h2>
        </div>
        
        <div className="flex-grow overflow-y-auto">
          <div className={categoryStyle}>
            Channels
            <Tooltip label="Add Channel" position="right">
              <ActionIcon 
                onClick={addChat} 
                variant="subtle" 
                color={darkMode ? "gray" : "dark"}
                className="hover:bg-gray-600 pointer-events-none hover:pointer-events-none"
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
