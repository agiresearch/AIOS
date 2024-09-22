import AgentPage, { Agent } from "./agent";


export default async function Page({ params }: { params: { name: string } }) {
    // let agentInfo: Agent;

    const res = await fetch(`https://agenthub-lite.vercel.app//api/get_agent_by_name?name=${params.name}`);
    const agentInfo: Agent = await res.json();

    return <AgentPage agent={agentInfo} />
}