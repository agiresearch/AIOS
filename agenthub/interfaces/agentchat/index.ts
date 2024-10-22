export interface Message {
    thinking: boolean | undefined;
    id: number;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    attachments?: string[]; // Array of file names or URLs
}

export interface Chat {
    id: number;
    name: string;
}

