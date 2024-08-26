/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import { Button } from "@nextui-org/react"

import {
    Dropdown,
    DropdownTrigger,
    DropdownMenu,
    DropdownSection,
    DropdownItem
} from "@nextui-org/dropdown";

import { ChevronsUpDown } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";

interface SettingsInterface {
    // exportPresets: (a: string) => void
}

export const Settings: React.FC<SettingsInterface> = () => {
    

    return <div className='h-full w-[15%] bg-inherit flex flex-col border-l-1 border-[rgba(153, 153, 153, 0.5)] p-6'>
       
    </div>
}