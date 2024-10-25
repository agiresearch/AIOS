'use client'

import React, { useCallback, useState, useEffect, useRef } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import HardBreak from '@tiptap/extension-hard-break';
import Placeholder from '@tiptap/extension-placeholder';
import Mention from '@tiptap/extension-mention'
import { ActionIcon, Group, Paper, Text as MantineText, useMantineTheme, ScrollArea, Image, Box, Overlay } from '@mantine/core';
import { Send, Plus, X, FileIcon } from 'lucide-react';

import suggestion from './Suggestion'
import { baseUrl, serverUrl } from '@/lib/env';
import axios from 'axios';

export interface ChatEditorProps {
  onSend: (content: string, attachments: File[]) => void;
  darkMode: boolean;
}



export const ChatEditor: React.FC<ChatEditorProps> = ({ onSend, darkMode }) => {
  const [attachments, setAttachments] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const theme = useMantineTheme();
  const [agents, setAgents] = useState([]);

  useEffect(() => {


    const _ = async () => {
      const response = await axios.post(`${baseUrl}/api/proxy`, {
          type: 'GET',
          url: `${serverUrl}/get_all_agents`,
      });
      setAgents(response.data.agents)
  }
  _()
  }, [])

  let currentStyleElement: HTMLStyleElement | null = null;

  const loadStyle = async (isDarkMode: boolean) => {
    // Remove the current style element if it exists
    if (currentStyleElement && currentStyleElement.parentNode) {
      currentStyleElement.parentNode.removeChild(currentStyleElement);
    }

    const fetchStyle = async (isDarkMode: boolean) => {
      const response = await fetch(isDarkMode ? '/MentionListV2Dark.scss' : '/MentionListV2Light.scss');
      return await response.text();
    };

    // Import the new style
    const style = await fetchStyle(isDarkMode)

    // Create a new style element
    currentStyleElement = document.createElement('style');
    currentStyleElement.textContent = style;
    document.head.appendChild(currentStyleElement);
  };

  useEffect(() => {
    loadStyle(darkMode);
  }, [darkMode])
  

  const editor = useEditor({
    extensions: [
      Document,
      Paragraph,
      Text,
      HardBreak.configure({
        HTMLAttributes: {
          class: 'my-2',
        },
      }),
      Placeholder.configure({
        placeholder: 'Type a message...',
      }),
      Mention.configure({
        HTMLAttributes: {
          class: 'mention',
        },
        suggestion,
      }),
    ],
    editorProps: {
      attributes: {
        class: `focus:outline-none p-2 min-h-[40px] max-h-[300px] overflow-y-auto ${
          darkMode ? 'text-white' : 'text-gray-800'
        }`,
      },
    },
  });

  const handleSend = useCallback(() => {
    if (editor) {
      const content = editor.getHTML();
      if (content.trim() !== '<p></p>' || attachments.length > 0) {
        onSend(content, attachments);
        editor.commands.setContent('');
        setAttachments([]);
        setPreviews([]);
      }
    }
  }, [editor, attachments, onSend]);

  const handleAttachment = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const newAttachments = Array.from(files);
      setAttachments(prev => [...prev, ...newAttachments]);
      
      newAttachments.forEach(file => {
        if (file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            setPreviews(prev => [...prev, e.target?.result as string]);
          };
          reader.readAsDataURL(file);
        } else {
          setPreviews(prev => [...prev, '']);
        }
      });
    }
  }, []);

  const removeAttachment = useCallback((index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
    setHoverIndex(null); // Reset hover state after removal
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    };

    editor?.view.dom.addEventListener('keydown', handleKeyDown);

    return () => {
      editor?.view.dom.removeEventListener('keydown', handleKeyDown);
    };
  }, [editor, handleSend]);

  const openFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <Paper 
      className={`p-2 ${darkMode ? '!bg-gray-800' : '!bg-white'} rounded-lg w-[90%]`}
      style={{
        border: `1px solid ${darkMode ? theme.colors.gray[7] : theme.colors.gray[3]}`,
        boxShadow: `0 2px 10px ${darkMode ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.1)'}`,
      }}
    >
      {attachments.length > 0 && (
        <ScrollArea className="mb-2 max-h-[150px]">
          <Group gap="xs" className="p-1">
            {attachments.map((file, index) => (
              <Box
                key={index}
                className="relative rounded-md overflow-hidden"
                style={{
                  width: 80,
                  height: 80,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                }}
                onMouseEnter={() => setHoverIndex(index)}
                onMouseLeave={() => setHoverIndex(null)}
              >
                {previews[index] ? (
                  <Image
                    src={previews[index]}
                    alt={file.name}
                    width={80}
                    height={80}
                    fit="cover"
                    style={{ objectFit: 'cover', width: '100%', height: '100%' }}
                  />
                ) : (
                  <div className={`flex flex-col items-center justify-center h-full p-2 ${
                    darkMode ? 'bg-gray-700 text-gray-200' : 'bg-gray-100 text-gray-800'
                  }`}>
                    <FileIcon size={24} className="mb-1" />
                    <MantineText size="xs" className="text-center truncate w-full">
                      {file.name}
                    </MantineText>
                  </div>
                )}
                {hoverIndex === index && (
                  <Overlay opacity={0.6} color="#000" zIndex={5}>
                    <ActionIcon
                      size="md"
                      variant="filled"
                      color="red"
                      className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                      onClick={(e) => {
                        console.log('hi')
                        e.stopPropagation(); // Prevent event bubbling
                        removeAttachment(index);
                      }}
                    >
                      <X size={16} />
                    </ActionIcon>
                  </Overlay>
                )}
              </Box>
            ))}
          </Group>
        </ScrollArea>
      )}
      <div className={`flex items-center rounded-md ${
        darkMode ? 'bg-gray-700' : 'bg-gray-100'
      }`}
      style={{
        boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.1)',
      }}
      >
        <ActionIcon
          onClick={openFileInput}
          variant="subtle"
          color={darkMode ? 'gray' : 'dark'}
          className="ml-2 hover:bg-opacity-10 hover:bg-gray-400 transition-colors"
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            border: `1px solid ${darkMode ? theme.colors.gray[6] : theme.colors.gray[4]}`,
          }}
        >
          <Plus size={20} />
        </ActionIcon>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleAttachment}
          multiple
        />
        <Box className="flex-grow">
          <EditorContent editor={editor} />
        </Box>
        <ActionIcon
          onClick={handleSend}
          variant="filled"
          color={theme.primaryColor}
          className="mx-2 transition-colors"
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            backgroundColor: (editor && editor.getText().trim() !== '') || attachments.length > 0 ? theme.colors[theme.primaryColor][6] : 'transparent',
            color: (editor && editor.getText().trim() !== '') || attachments.length > 0 ? 'white' : theme.colors.gray[5],
            boxShadow: (editor && editor.getText().trim() !== '') || attachments.length > 0 ? '0 2px 4px rgba(0,0,0,0.2)' : 'none',
          }}
        >
          <Send size={16} />
        </ActionIcon>
      </div>
    </Paper>
  );
};