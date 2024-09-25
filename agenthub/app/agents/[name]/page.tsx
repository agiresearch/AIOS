import { baseUrl } from "@/lib/env";
import AgentPage, { Agent } from "./agent";


export default async function Page({ params }: { params: { name: string } }) {
    // let agentInfo: Agent;
    // console.log(params.name.split('%2B'))
    const res = await fetch(`${baseUrl}/api/get_agent_by_name_and_version?name=${params.name.split('%2B')[0]}&version=${params.name.split('%2B')[1]}`);
    const agentInfo: Agent = await res.json();

    console.log(agentInfo)

    return <AgentPage agent={agentInfo} />
}