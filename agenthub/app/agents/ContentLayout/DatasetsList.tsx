import AgentCard from './AgentCard'
import { AgentListGenerator } from '../const'
import { DatasetsPagination } from './DatasetsPagination'
import { DatasetsHeader } from './DatasetsHeader'



export default async function DatasetsList(
  { searchParams }:
    { searchParams: { [key: string]: string | string[] | undefined } }) {

      let page;
  if (searchParams==undefined) {
    page = 0;
  } else {
    page = parseInt(searchParams.p as string)
  }

  let AgentList = await AgentListGenerator();
  const start = page*15;
  let end = page*15+15
  // let [start, end] = [page*15, page*15+15]

  if (end >= AgentList.length) {
    end = AgentList.length
  }
  console.log(start, end)
  AgentList = AgentList.slice(start, end)
  

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
      <DatasetsPagination page={page+1} maxPage={AgentList.length/15} />
    </section>
  )
}