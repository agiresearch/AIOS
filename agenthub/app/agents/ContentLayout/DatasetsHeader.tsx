import { FilterSVG, InnerDatasetSVG, SortSVG } from '@/ui/svgs'

export function DatasetsHeader() {
  return (
    <div className="mb-4 items-center space-y-3 md:flex md:space-y-0 lg:mb-6">
      <div className="flex items-center text-lg">
        <h1>Datasets</h1>
        <div className="ml-3 w-16 font-normal text-gray-400">49,419</div>
      </div>
      <div className="flex-1 md:mx-4">
        <div className="relative w-full md:max-w-xs">
          <InnerDatasetSVG />
          <input
            className="w-full rounded-full border border-gray-200 text-sm placeholder-gray-400 shadow-inner outline-none focus:shadow-xl focus:ring-1 focus:ring-inset dark:bg-gray-950 h-7 pl-7"
            placeholder="Filter by name"
            type="search"
            value=""
            readOnly
          />
        </div>
      </div>
      <a href="/search/full-text?type=dataset" className="btn mr-2 rounded-full text-sm opacity-80 hover:opacity-100">
        <span className="mr-1.5 rounded bg-blue-500/10 px-1 text-xs leading-tight text-blue-700 dark:text-blue-200">
          new
        </span>
        Full-text search
      </a>
      <div>
        <button className="btn mr-2 inline-flex text-sm lg:hidden " type="button">
          <FilterSVG />
          Add filters
        </button>
        <div className="relative inline-block">
          <button className=" btn w-full cursor-pointer text-sm" type="button">
            <SortSVG />
            Sort:  Trending
          </button>
        </div>
      </div>
    </div>
  )
}