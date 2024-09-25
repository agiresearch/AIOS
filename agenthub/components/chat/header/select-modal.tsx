
import { ChevronDown, Sparkles, Zap } from "lucide-react";

import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/chat/ui/popover"

import { useState } from "react";
import { GPTModel } from "./types";
import { Checkbox } from "@/components/chat/ui/checkbox";
// import { UpgradeModal } from "./upgrade-modal";


export const SelectModal = () => {
    const [openSelect, setOpenSelect] = useState(false);
    const [openUpgradeModal, setOpenUpgradeModal] = useState(false);


    const isSubscribed = true;

    const GPTVersionText = "4";

    const handleClick = (model: GPTModel) => {
        // if gpt-3, just select and return
        
        // setOpenSelect(!openSelect);
    }

    const toggleOpen = () => {
        // setOpenSelect(!openSelect);
    }

    return (
        <>
            {/* <UpgradeModal
                open={openUpgradeModal}
                setOpen={setOpenUpgradeModal}
            /> */}
            <Popover open={openSelect}>
                <PopoverTrigger
                    onClick={toggleOpen}
                    className="flex space-x-2 font-semibolditems-center"
                >
                    <p>AIOS</p>
                    <p className="text-white/50">v1 Beta</p>
                    <ChevronDown className="text-white/50 w-5 h-5" />
                </PopoverTrigger>
                <PopoverContent className="flex flex-col border-0 bg-neutral-700 text-white p-3 space-y-4">
                    <div
                        onClick={() => handleClick(GPTModel.GPT3)}
                        className="flex items-center text-start cursor-pointer rounded-md justify-start space-x-2 p-2 w-full h-full hover:bg-neutral-600"
                    >
                        <Zap className="w-6 h-6" />
                        <div className="w-full">
                            <p className="font-normal">GPT 3.5</p>
                            <p className="text-white/70">Great for everyday tasks.</p>
                        </div>
                        <Checkbox id="terms1" checked={false} />
                    </div>

                    <div
                        onClick={() => handleClick(GPTModel.GPT4)}
                        className="flex items-center text-start cursor-pointer rounded-md justify-start space-x-2 p-2 w-full h-full hover:bg-neutral-600"
                    >
                        <Sparkles className="w-6 h-6" />
                        <div className="w-full">
                            <p className="font-normal">GPT-4</p>
                            <p className="text-white/70">Our smartest and best model</p>
                            {!isSubscribed &&
                                <div className="w-full p-2 rounded-lg text-white text-xs text-center font-normal cursor-pointer bg-purple-500 active:bg-purple-700 mt-1.5">
                                    Upgrade to plus
                                </div>
                            }
                        </div>
                        <Checkbox id="terms2" checked={true} />
                    </div>
                </PopoverContent>
            </Popover>
        </>
    )
}