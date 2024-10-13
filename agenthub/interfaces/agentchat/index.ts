export interface Message {
    thinking: boolean | undefined;
    id: number;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    attachments?: string[]; // Array of file names or URLs
  }
export interface HeaderProps {
    darkMode: boolean;
    setDarkMode: React.Dispatch<React.SetStateAction<boolean>>;
}

export interface MessageBubbleProps {
    message: Message;
    darkMode: boolean;
    index: number;
    isThinking?: boolean;
  }

export interface MessageListProps {
    messages: Message[];
    darkMode: boolean;
}

export interface InputAreaProps {
    input: string;
    setInput: React.Dispatch<React.SetStateAction<string>>;
    handleSend: () => void;
    darkMode: boolean;
}

export interface Chat {
    id: number;
    name: string;
}

export interface SidebarProps {
    chats: Chat[];
    activeChat: number;
    setActiveChat: (id: number) => void;
    addChat: () => void;
    updateChatName: (chatId: number, newName: string) => void;
    darkMode: boolean;
}