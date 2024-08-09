import React, { memo, ReactNode } from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import { FiCloud } from 'react-icons/fi';

export type ConversationalNodeData = {

};

const Conversational = ({ data }: NodeProps<ConversationalNodeData>) => {
    return (
        <>
            <div className="cloud gradient">
                <div>
                    <FiCloud />
                </div>
            </div>
            <div className="wrapper gradient">
                <div className="conversational inner">
                    <div className='flex flex-col w-full h-full gap-y-2 items-center justify-center'>
                        <p className='text-white text-xl w-full text-center'>Conversational Agent</p>
                    </div>

                    <Handle className='conversational-handle' type="target" position={Position.Left} />
                    <Handle className='conversational-handle' type="source" position={Position.Right} />
                </div>
            </div>
        </>
    );
};


export default memo(Conversational);