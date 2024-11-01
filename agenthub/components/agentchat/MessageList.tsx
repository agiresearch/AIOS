import { Message } from "@/interfaces/agentchat";
import { MessageBubble } from "./MessageBubble";

export interface MessageListProps {
    messages: Message[];
    darkMode: boolean;
}


export const MessageList: React.FC<MessageListProps> = ({ messages, darkMode }) => (
    <div className={`flex-grow overflow-y-auto ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="py-4 space-y-1">
        {messages.map((message, index) => (
          <MessageBubble key={message.id} message={message} darkMode={darkMode} index={index} isThinking={message.thinking} />
        ))}
      </div>
    </div>
  );