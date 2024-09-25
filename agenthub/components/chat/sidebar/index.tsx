import { ChatList } from "./chat-list";
import { NewChatButton } from "./new-chat-button";
// import { UpgradePlanButton } from "./upgrade-plan-button";

export const Sidebar = () => {
    return (
        <div className="h-full hidden lg:flex lg:flex-col lg:w-[300px] bg-neutral-950 p-4 z-[500000]">
            <NewChatButton />
            <ChatList />
            {/* <UpgradePlanButton /> */}
        </div>
    );
};