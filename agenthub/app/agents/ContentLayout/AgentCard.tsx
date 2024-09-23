import { DownloadSVG, FavoriteSVG, TableViewerSVG, AgentSVG } from '@/ui/svgs'
import { AgentItem } from '../type'
import { formatDate } from '@/app/utils'

export interface AgentCardProps {
  item: AgentItem
}

export default function AgentCard({ item }: AgentCardProps) {
  // const { title, tableType, dateTime, timeTitle, date, downloads, favorites } = item
  const date = new Date(item.createdAt)

  return (
    <article className="overview-card-wrapper group  ">
      <a className="block p-2" href={`/agents/${item.name}`}>
        <header className="flex items-center mb-0.5" title={item.name}>
          <AgentSVG />
          <h4 className="text-md truncate font-mono text-black dark:group-hover:text-yellow-500 group-hover:text-blue-500 text-smd">
            {item.name}
          </h4>
        </header>
        <div className="mr-1 flex items-center overflow-hidden whitespace-nowrap text-sm leading-tight text-gray-400">
          <TableViewerSVG />

          {'Preview'}
          <span className="px-1.5 text-gray-300">• </span>
          <span className="truncate">
            Updated {' '}
            <time dateTime={date.toISOString()} title={'Time String'}>
              {formatDate(date.toISOString())}
            </time>
            {/* <div>{item.createdAt.toUTCString()}</div> */}
          </span>
          <span className="px-1.5 text-gray-300">• </span>
          <DownloadSVG />
          {item.numDownloads}
          <span className="px-1.5 text-gray-300">• </span>
          <FavoriteSVG />
          {item.numFavorites}
        </div>
      </a>
    </article>
  )
}