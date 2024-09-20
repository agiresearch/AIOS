import AgentPage, { Agent } from "./agent";


export default async function Page({ params }: { params: { name: string } }) {
    let agentInfo: Agent;

    const res = await fetch(`http://localhost:3000/api/get_agent_by_name?name=${params.name}`);
    agentInfo = await res.json();

    return <AgentPage agent={agentInfo} />
}