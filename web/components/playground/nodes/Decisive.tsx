'use client'

import React, { memo, ReactNode, useEffect, useState } from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import { FaQuestion } from 'react-icons/fa6';

export type DecisiveNodeData = {
    setter: (s: string) => void
  };


const Decisive = ({ data }: NodeProps<DecisiveNodeData>) => {
    const [text, setText] = useState('')

    useEffect(() => {
      if (text)
        data.setter(text)
    }, [text])

    return (
        <>
            <div className="cloud gradient">
                <div>
                    <FaQuestion />
                </div>
            </div>
            <div className="wrapper gradient">
                <div className="decisive inner">
                    <div className='flex flex-col w-full h-full gap-y-2 mb-3'>
                        <h1 className='w-full text-center text-lg text-white'>Decisive Agent</h1>
                        <textarea className='w-full h-full bg-white text-black rounded-lg text-xs p-3'
                            rows={3}
                            value={text} 
                            onChange={e => setText(e.target.value)}
                            placeholder={'Enter Agent Instructions Here'}>

                        </textarea>
                    </div>

                    <Handle className='decisive-handle' type="target" position={Position.Left} />
                    <div className='w-full flex flex-row justify-between'>
                        <Handle
                            className='decisive-handle-a'
                            id="yes"
                            type="source"
                            position={Position.Right}
                        />
                        <Handle
                            className='decisive-handle-b'
                            id="no"
                            type="source"
                            position={Position.Bottom}
                        />
                    </div>


                </div>
            </div>
        </>
    );
};

export default memo(Decisive);
