import DatasetCard from './DatasetCard'
import { DatasetList } from '../const'
import { DatasetsPagination } from './DatasetsPagination'
import { DatasetsHeader } from './DatasetsHeader'

export default function DatasetsList() {
  return (
    <section className="pt-8 border-gray-100 col-span-full lg:col-span-6 xl:col-span-7 pb-12">
      <DatasetsHeader />
      <div className="relative">
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {DatasetList.map((datasetItem, index) => {
            return <DatasetCard key={index} item={datasetItem} />
          })}
        </div>
      </div>
      <DatasetsPagination />
    </section>
  )
}