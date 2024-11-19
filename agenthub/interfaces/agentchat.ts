export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    attachments?: string[];
    thinking?: boolean;
}

export interface Chat {
    id: number;
    name: string;
    messages: Message[];
}
