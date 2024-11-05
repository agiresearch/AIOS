'use client'

import React, { useState, useRef, useEffect } from 'react';

import { ActionIcon, CopyButton } from '@mantine/core';
import { Clipboard, Check } from 'lucide-react';

import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import rehypeRaw from 'rehype-raw';

// Improved Markdown component
interface MarkdownProps {
    content: string;
    darkMode: boolean;
    animation: boolean;
}

export const Markdown: React.FC<MarkdownProps> = ({ content, darkMode, animation }) => {
    const [displayedText, setDisplayedText] = useState('');
    const animationRef = useRef<number | null>(null);
    const currentIndexRef = useRef(0);

    useEffect(() => {
        if (animation) {
            let lastTimestamp: number | null = null;

            const streamText = (timestamp: number) => {
                if (lastTimestamp === null) {
                    lastTimestamp = timestamp;
                }

                const elapsed = timestamp - lastTimestamp;

                if (elapsed >= 10) { // Reduced minimum delay between updates from 30ms to 10ms
                    if (currentIndexRef.current < content.length) {
                        // Increased chunk size for faster typing
                        const chunkSize = Math.floor(Math.random() * 4) + 2; // Now 2-5 characters at once
                        const nextChunk = content.slice(currentIndexRef.current, currentIndexRef.current + chunkSize);

                        setDisplayedText(prevText => prevText + nextChunk);
                        currentIndexRef.current += chunkSize;

                        // Reduced delays for a faster animation
                        let delay = Math.floor(Math.random() * 20) + 10; // Base delay between 10-30ms

                        // Shorter pauses for punctuation
                        if (nextChunk.includes('.') || nextChunk.includes('!') || nextChunk.includes('?')) {
                            delay += Math.floor(Math.random() * 100) + 50; // Reduced to 50-150ms for major punctuation
                        } else if (nextChunk.includes(',') || nextChunk.includes(';')) {
                            delay += Math.floor(Math.random() * 50) + 25; // Reduced to 25-75ms for minor punctuation
                        }

                        // Reduced delay for word complexity
                        if (nextChunk.length > 5) {
                            delay += nextChunk.length * 3; // Reduced to 3ms per character
                        }

                        lastTimestamp = timestamp + delay;
                    }
                }

                animationRef.current = requestAnimationFrame(streamText);
            };

            animationRef.current = requestAnimationFrame(streamText);

            return () => {
                if (animationRef.current !== null) {
                    cancelAnimationFrame(animationRef.current);
                }
            };
        } else {
            setDisplayedText(content);
        }

    }, [content]);


    return (
        <ReactMarkdown
            rehypePlugins={[rehypeRaw]}
            components={{
                code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match && (props as any).inline;
                    return isInline ? (
                        <code className={`${className} ${darkMode ? '!bg-gray-700' : '!bg-gray-200'} rounded px-1 py-0.5`} {...props}>
                            {children}
                        </code>
                    ) : (
                        <div className="relative">
                            <div className="flex justify-between items-center px-4 py-2 bg-gray-800 rounded-t-md">
                                <span className="text-sm !text-[#e06c75]">{match ? match[1] : 'text'}</span>
                                <CopyButton value={String(children).replace(/\n$/, '')}>
                                    {({ copied, copy }) => (
                                        <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
                                            {copied ? <Check size={16} /> : <Clipboard size={16} />}
                                        </ActionIcon>
                                    )}
                                </CopyButton>
                            </div>
                            <SyntaxHighlighter
                                language={match ? match[1] : 'text'}
                                style={atomDark as any}
                                PreTag="div"
                                className="rounded-b-md"
                            >
                                {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                        </div>
                    );
                },
                p: ({ children, ...props }) => <p className="mb-4 last:mb-0" {...props}>{children}</p>,
                br: ({ ...props }) => <br {...props} />,
                ul: ({ children }) => <ul className="list-disc pl-6 mb-4">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-6 mb-4">{children}</ol>,
                li: ({ children }) => <li className="mb-2">{children}</li>,
                h1: ({ children }) => <h1 className="text-2xl font-bold mb-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-bold mb-3">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-bold mb-2">{children}</h3>,
                blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4">{children}</blockquote>
                ),
            }}
        >
            {displayedText}
        </ReactMarkdown>
    );
};