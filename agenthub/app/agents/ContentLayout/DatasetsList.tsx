import AgentCard from './AgentCard'
import { AgentListGenerator, DatasetList } from '../const'
import { DatasetsPagination } from './DatasetsPagination'
import { DatasetsHeader } from './DatasetsHeader'



export default async function DatasetsList() {
    

    const AgentList = await AgentListGenerator();

  return (
    <section className="pt-8 border-gray-100 col-span-full lg:col-span-6 xl:col-span-7 pb-12">
      <DatasetsHeader />
      <div className="relative">
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {AgentList.map((agentItem, index) => {
            return <AgentCard key={index} item={agentItem} />
          })}
        </div>
      </div>
      <DatasetsPagination />
    </section>
  )
}