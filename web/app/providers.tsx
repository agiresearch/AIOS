'use client'

import { ReactFlowProvider } from "reactflow"
import {NextUIProvider} from '@nextui-org/react'


export function FlowProvider({ children }: { children: React.ReactNode }) {
    return (
        <ReactFlowProvider>
            <NextUIProvider>
            {children}
            </NextUIProvider>
        </ReactFlowProvider>
    )
}