'use client'

import React, { useCallback, useRef } from 'react';
import ReactFlow, { Controls, useNodesState, useEdgesState, addEdge, Node, Edge, useReactFlow } from 'reactflow';
import { FiFile } from 'react-icons/fi';

import 'reactflow/dist/base.css';
import '@/components/playground/rewrites.css';
import TurboEdge from '@/components/playground/Edge';
import FunctionIcon from '@/components/playground/FunctionIcon';
import Sidebar from '@/components/playground/Sidebar';
import Decisive from '@/components/playground/nodes/Decisive';
import Conversational from '@/components/playground/nodes/Conversational';
import Laborious from '@/components/playground/nodes/Laborious';
import { Connection, createWorkflowStructure } from '@/agents/graph';

const initialNodes: Node<any>[] = [];

import { AgentContainer } from '@/components/AgentContainer';

// [
//     {
//         id: '1',
//         position: { x: 0, y: 0 },
//         data: { icon: <FunctionIcon />, title: 'readFile', subline: 'api.ts' },
//         type: 'turbo',
//     },
//     {
//         id: '2',
//         position: { x: 250, y: 0 },
//         data: { icon: <FunctionIcon />, title: 'bundle', subline: 'apiContents' },
//         type: 'turbo',
//     },
//     {
//         id: '3',
//         position: { x: 0, y: 250 },
//         data: { icon: <FunctionIcon />, title: 'readFile', subline: 'sdk.ts' },
//         type: 'turbo',
//     },
//     {
//         id: '4',
//         position: { x: 250, y: 250 },
//         data: { icon: <FunctionIcon />, title: 'bundle', subline: 'sdkContents' },
//         type: 'turbo',
//     },
//     {
//         id: '5',
//         position: { x: 500, y: 125 },
//         data: { icon: <FunctionIcon />, title: 'concat', subline: 'api, sdk' },
//         type: 'turbo',
//     },
//     {
//         id: '6',
//         position: { x: 750, y: 125 },
//         data: { icon: <FiFile />, title: 'fullBundle' },
//         type: 'turbo',
//     },
// ];

const initialEdges: Edge[] = [];

// [{
//     id: 'e1-2',
//     source: '1',
//     target: '2',
// },
// ]


const nodeTypes = {
    decisive: Decisive,
    conversable: Conversational,
    laborious: Laborious,
};

const edgeTypes = {
    turbo: TurboEdge,
};

const defaultEdgeOptions = {
    type: 'turbo',
    markerEnd: 'edge-circle',
};

let id = 0;
const getId = () => `dndnode_${id++}`;

const Flow = () => {
    const reactFlowWrapper = useRef(null);
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const { screenToFlowPosition } = useReactFlow();

    const onConnect = useCallback((params: any) => setEdges((els) => addEdge(params, els)), []);

    const onDragOver = useCallback((event: any) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: any) => {
            event.preventDefault();

            const type = event.dataTransfer.getData('application/reactflow');

            if (typeof type === 'undefined' || !type) {
                return;
            }

            const position = screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            let data = {};

            if (!(type == 'conversable')) {
                data = { setter: (s: string) => console.log(s) };
            }

            const newNode = {
                id: getId(),
                type: type,
                position,
                data: {
                    ...data
                },
            };

            setNodes((nds) => nds.concat(newNode));
        },
        [screenToFlowPosition],
    );

    return (
        <main className='w-screen h-screen overflow-hidden flex flex-row gap-x-0'>
            <div className='w-[80vw] h-[100vh] flex flex-col'>
                <div style={{ width: '80vw', height: '75vh' }} ref={reactFlowWrapper}>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        fitView
                        nodeTypes={nodeTypes}
                        edgeTypes={edgeTypes}
                        defaultEdgeOptions={defaultEdgeOptions}
                        onDrop={onDrop}
                        onDragOver={onDragOver}
                    >
                        <Controls showInteractive={false} />
                        <svg>
                            <defs>
                                <linearGradient id="edge-gradient">
                                    <stop offset="0%" stopColor="#ae53ba" />
                                    <stop offset="100%" stopColor="#2a8af6" />
                                </linearGradient>

                                <marker
                                    id="edge-circle"
                                    viewBox="-5 -5 10 10"
                                    refX="0"
                                    refY="0"
                                    markerUnits="strokeWidth"
                                    markerWidth="10"
                                    markerHeight="10"
                                    orient="auto"
                                >
                                    <circle stroke="#2a8af6" strokeOpacity="0.75" r="2" cx="0" cy="0" />
                                </marker>
                            </defs>
                        </svg>
                    </ReactFlow>
                </div>
                <div style={{ width: '80vw', height: '25vh' }} className='bg-[#c3bfbf]'>

                </div>
            </div>

            <div className='bg-[#212020] w-[20vw] h-screen rounded-md border-white border-double border-[1.5px]'>
                <Sidebar />
                <div className='flex flex-row justify-center items-center w-full h-[20vh]'>
                    <button onClick={() => {
                        const connections = edges.map(edge => ({
                            source: edge.source,
                            sourceHandle: edge.sourceHandle, target: edge.target
                        } as Connection))

                        console.log(connections)

                        // const workflow = createWorkflowStructure(connections);
                        // AgentContainer('math_agent');

                        // console.log(workflow)
                    }}>
                        Run Simulation
                    </button>
                </div>
            </div>
        </main>
    );
};

export default Flow;
