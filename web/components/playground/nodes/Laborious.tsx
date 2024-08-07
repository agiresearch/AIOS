'use client'

import React, { memo, ReactNode, useEffect, useState } from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import { FaHourglass } from 'react-icons/fa';

export type LaboriousNodeData = {
  setter: (s: string) => void
};

const Laborious = ({ data }: NodeProps<LaboriousNodeData>) => {
  const [text, setText] = useState('')

  useEffect(() => {
    if (text)
      data.setter(text)
  }, [text])

  return (
    <>
      <div className="cloud gradient">
        <div>
          <FaHourglass />
        </div>
      </div>
      <div className="wrapper laborious-gradient min-w-[300px]">
        <div className="inner">
          <div className='flex flex-col w-full h-full gap-y-2'>
            <h1 className='w-full text-center text-lg text-white'>Laborious Agent</h1>
            <textarea className='w-full h-full bg-white text-black rounded-lg text-sm p-3' 
            rows={5} 
            value={text} 
            onChange={e => setText(e.target.value)}
            placeholder={'Enter Agent Instructions Here'}>
           
            </textarea>
          </div>
        
          <Handle className='laborious-handle' type="target" position={Position.Left} />
          <Handle className='laborious-handle' type="source" position={Position.Right} />
        </div>
      </div>
    </>
  );
};

export default memo(Laborious);