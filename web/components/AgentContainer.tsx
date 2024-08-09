import { Draggable } from "@hello-pangea/dnd";
import { ReactNode } from "react";

interface AgentContainerProps {
  name: string;
  unique: string;
  index: number;
  icon: React.ReactNode
}

export const AgentContainer: React.FC<AgentContainerProps> = ({
  name,
  unique,
  index,
  icon,
}) => {
  return (
    <Draggable draggableId={`${index}-${unique}`} index={index}>
      {(provided) => (
        <div
        className='w-full h-fit p-4 rounded-lg drop-shadow-md flex items-center justify-center bg-black border-white border-1 border-dashed hover:bg-[#272525]'
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          ref={provided.innerRef}
        >
        <p className='text-white text-2xl flex gap-x-3 justify-center items-center'>{icon as ReactNode} {' '}{name}</p>
        </div>
      )}
    </Draggable>
  );
};
