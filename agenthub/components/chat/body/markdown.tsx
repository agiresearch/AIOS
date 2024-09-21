import ReactMarkdown from 'react-markdown';
import { toast } from 'sonner';
import copy from "copy-to-clipboard";
import { Clipboard } from 'lucide-react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { gruvboxDark } from 'react-syntax-highlighter/dist/cjs/styles/hljs';

interface IProps {
    content: string;
}

export default function Markdown({ content }: IProps) {
    const handleCopy = (text: string) => {
        copy(text);
        toast.success("Copied to clipboard;");
    }

    return (
        <ReactMarkdown
            components={{
                code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return match ? (
                        <div>
                            <div className='flex w-full justify-end bg-white/5 p-2 rounded-t-md'>
                                <button onClick={() => handleCopy(String(children).replace(/\n$/, ''))}>
                                    <Clipboard className='text-white/20 w-4 h-4' />
                                </button>
                            </div>
                            <SyntaxHighlighter
                                language={match[1]}
                                style={gruvboxDark}
                            >
                                {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                        </div>
                    ) : (
                        <code className={className} {...props}>
                            {children}
                        </code>
                    )
                },
            }}
        >{content}</ReactMarkdown>
    )
}