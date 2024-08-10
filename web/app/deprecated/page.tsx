'use client'
import { AgentContainer } from "@/components/AgentContainer";
import { StrictModeDroppable } from "@/components/rewrites/StrictModeDroppable";
import Image from "next/image";
import { Calculator, LucideProps } from "lucide-react";
import { ReactNode, useState } from "react";

import { DragDropContext, Droppable, OnDragEndResponder } from '@hello-pangea/dnd'

export default function Home() {
  const [agents, setAgents] = useState<Record<string, string | ReactNode>[]>([{
    name: 'Math Agent',
    icon: <Calculator />
  },{
    name: 'Story Agent',
    icon: <Calculator />
  },
  ]);

  function swap(array_: any[], index1: number, index2: number): any[] {
    let array = [...array_]
    // Ensure the indexes are within bounds
    if (index1 >= 0 && index1 < array.length && index2 >= 0 && index2 < array.length) {
      // Swap using a temporary variable
      let temp = array[index1];
      array[index1] = array[index2];
      array[index2] = temp;
    } else {
      console.error("Invalid indexes provided");
    }

    return array;
  }

  const onDragEnd = (result: any) => {
    console.log(result);

    const destination = result.destination.index;
    const source = result.source.index;

    setAgents((prev) => {
      return swap(prev, source, destination)
    })
  }

  return (
    <DragDropContext
      // onDragStart={}
      // onDragUpdate={}
      onDragEnd={onDragEnd}
    >
      <main className="flex min-h-screen flex-row items-center justify-between p-8 max-h-screen h-screen w-full overflow-hidden">
        <StrictModeDroppable droppableId={'agent-counter-tab'} >
          {(provided) => (
            <div className='w-1/4 h-full flex flex-col px-3 py-3 gap-y-3'
              {...provided.droppableProps}
              ref={provided.innerRef}>
              {agents.map((agent, index: number) => (<AgentContainer key={`${index}-agentcountertabs`} name={agent.name as string} index={index} unique={'agentcountertabs'} icon={agent.icon as ReactNode} />))}
            </div>)}
        </StrictModeDroppable>
        <div className='w-3/4 h-full' >

        </div>


        {/* <StrictModeDroppable droppableId={'123'} >
          {(provided) => (
            <div className='flex flex-col h-full rounded-lg bg-black border-white border-1 w-1/2 gap-y-2 p-4' {...provided.droppableProps} ref={provided.innerRef}>

              {agents.map((agent: string, index: number) => (<AgentContainer key={`${index}-agentcounter`} name={agent} index={index} />))}
              {provided.placeholder}
            </div>)}
        </StrictModeDroppable>
        <StrictModeDroppable droppableId={'245'} >
          {(provided) => (
            <div className='flex flex-col h-full rounded-lg bg-black border-white border-1 w-1/2 gap-y-2 p-4' {...provided.droppableProps} ref={provided.innerRef}>

              {agents.map((agent: string, index: number) => (<AgentContainer key={`${index}-agentcounter`} name={agent} index={index} />))}
              {provided.placeholder}
            </div>)}
        </StrictModeDroppable> */}

      </main>
    </DragDropContext>
  );
}
