'use client'

import Document from "@tiptap/extension-document";
import Mention from "@tiptap/extension-mention";
import Paragraph from "@tiptap/extension-paragraph";
import Text from "@tiptap/extension-text";
import { EditorContent, ReactRenderer, useEditor } from "@tiptap/react";
import React, { useEffect, useState } from "react";
import { MentionList } from "./MentionList";
// import StarterKit from '@tiptap/starter-kit'
import dynamic from "next/dynamic";

export interface EditorProps {
    callback: (s: string) => void
}

export const Editor: React.FC<EditorProps> = ({
    callback
}) => {
    const handleChange = (s: string) => {
        console.log('handling', s)
        callback(s);
    }

    const editor = useEditor({
        editorProps: { attributes: { class: "editor" } },
        immediatelyRender: false,
        extensions: [
            Document,
            Paragraph.configure({
                HTMLAttributes: { class: "paragraph" }
            }),
            Text,
            // StarterKit,
            Mention.configure({
                HTMLAttributes: { class: "mentionNode" },
                suggestion: {
                    render: () => {
                        //@ts-ignore
                        let reactRenderer: ReactRenderer;

                        return {
                            onStart: (props: any) => {
                                reactRenderer = new ReactRenderer(MentionList, {
                                    props,
                                    editor: props.editor
                                });
                            },

                            onUpdate(props: any) {
                                reactRenderer?.updateProps(props);
                            },

                            onKeyDown(props: any) {
                                if (props.event.key === "Escape") {
                                    reactRenderer?.destroy();
                                    return true;
                                }

                                return (reactRenderer?.ref as any)?.onKeyDown(props);
                            },

                            onExit() {
                                reactRenderer.destroy();
                            }
                        };
                    }
                }
            })
        ],
        onUpdate: ({ editor }) => {
            handleChange(editor.getText());
        },
    });

    const [isMounted, setIsMounted] = useState(false)

    useEffect(() => {
        setIsMounted(true)
    }, [])

    if (!isMounted) {
        return null // or a loading placeholder
    }

    return <EditorContent editor={editor} />;
    // return <div></div>
};
