export interface Connection {
    source: string;
    sourceHandle: string | null;
    target: string;
  }
  
  interface WorkflowNode {
    id: string;
    isDecision: boolean;
    next: {
      yes?: WorkflowNode;
      no?: WorkflowNode;
      default?: WorkflowNode;
    };
  }

  interface WorkflowStructure {
    nodes: Map<string, WorkflowNode>;
    startNodes: WorkflowNode[];
  }
  
  export function createWorkflowStructure(connections: Connection[]): WorkflowStructure {
    const nodes = new Map<string, WorkflowNode>();
    const targetSet = new Set<string>();
  
    for (const conn of connections) {
      if (!nodes.has(conn.source)) {
        nodes.set(conn.source, { id: conn.source, isDecision: false, next: {} });
      }
      if (!nodes.has(conn.target)) {
        nodes.set(conn.target, { id: conn.target, isDecision: false, next: {} });
      }
      
      if (conn.sourceHandle !== null) {
        nodes.get(conn.source)!.isDecision = true;
      }
  
      targetSet.add(conn.target);
    }
  
    for (const conn of connections) {
      const sourceNode = nodes.get(conn.source)!;
      const targetNode = nodes.get(conn.target)!;
  
      if (sourceNode.isDecision) {
        if (conn.sourceHandle === 'yes') {
          sourceNode.next.yes = targetNode;
        } else if (conn.sourceHandle === 'no') {
          sourceNode.next.no = targetNode;
        }
      } else {
        sourceNode.next.default = targetNode;
      }
    }

    console.log(targetSet);
  
    const startNodes = Array.from(nodes.values()).filter(node => !targetSet.has(node.id));
  
    return { nodes, startNodes };
  }
  
