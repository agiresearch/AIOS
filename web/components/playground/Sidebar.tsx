import React from 'react';

const Sidebar = () => {
  const onDragStart = (event: any, nodeType: any) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside className='w-full h-[80vh] flex flex-col p-4 gap-y-5'>
      <div className="text-white text-4xl w-full text-center">Editor</div>
      <div className="text-white text-2xl text-center p-3 rounded-lg bg-black border-[#d1c7c7] border-2 border-solid hover:scale-105 hover:cursor-move active:cursor-move" onDragStart={(event) => onDragStart(event, 'conversable')} draggable>
        Conversable Agent
      </div>
      <div className="text-white text-2xl text-center p-3 rounded-lg bg-black border-[#d1c7c7] border-2 border-solid hover:scale-105 hover:cursor-move active:cursor-move" onDragStart={(event) => onDragStart(event, 'laborious')} draggable>
        Laborious Agent
      </div>
      <div className="text-white text-2xl text-center p-3 rounded-lg bg-black border-[#d1c7c7] border-2 border-solid hover:scale-105 hover:cursor-move active:cursor-move" onDragStart={(event) => onDragStart(event, 'decisive')} draggable>
        Decisive Agent
      </div>
    </aside>
  );
};

export default Sidebar;