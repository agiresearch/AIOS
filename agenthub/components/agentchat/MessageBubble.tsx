import { Message } from "@/interfaces/agentchat";
import { Loader } from "@mantine/core";
import { Markdown } from "./Markdown";

export interface MessageBubbleProps {
  message: Message;
  darkMode: boolean;
  index: number;
  isThinking?: boolean;
}

const AgentLoader = () => {
  return <div className="flex items-center space-x-2 animate-pulse">
      <Loader size="sm" />
      <span>Agent is thinking...</span>
  </div>
}

// Updated MessageBubble component
export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, darkMode, index, isThinking = false }) => (
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
          {isThinking ? <AgentLoader /> : <Markdown content={message.text} darkMode={darkMode} animation={message.sender === 'user' ? false : true} />}
        </div>
      </div>
    </div>
  );