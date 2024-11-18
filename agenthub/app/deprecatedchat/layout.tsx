import { Sidebar } from "@/components/chat/sidebar";

interface ChatLayoutProps {
    children: React.ReactNode;
}

export default function ChatLayout({ children }: ChatLayoutProps) {
    return (
        <main className="flex h-[calc(100vh-65px)] text-white overflow-clip bg-neutral-800">
            <Sidebar />
            <div className="h-full w-full">
                {children}
            </div>
        </main>
    );
};