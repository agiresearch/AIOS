// import { UserButton } from "@clerk/clerk-react";
import { SelectModal } from "./select-modal";
// import { MobileSidebar } from "@/components/mobile-sidebar";

export const Header = () => {
    return (
        <div className="flex h-[50px] justify-start w-full p-5 pl-10">
            {/* <MobileSidebar /> */}
             <SelectModal />
            {/* <UserButton />  */}
        </div>
    );
};