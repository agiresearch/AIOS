import { DatasetSVG, DownloadSVG, FavoriteSVG, TablePreviewSVG, TableViewerSVG } from '@/ui/svgs'
import { DatasetItem } from '../type'

export interface DatasetCardProps {
  item: DatasetItem
}

export default function DatasetCard({ item }: DatasetCardProps) {
  const { title, tableType, dateTime, timeTitle, date, downloads, favorites } = item

  return (
    <article className="overview-card-wrapper group  ">
      <a className="block p-2" href={`/datasets/${title}`}>
        <header className="flex items-center mb-0.5" title={title}>
          <DatasetSVG />
          <h4 className="text-md truncate font-mono text-black dark:group-hover:text-yellow-500 group-hover:text-red-600 text-smd">
            {title}
          </h4>
        </header>
        <div className="mr-1 flex items-center overflow-hidden whitespace-nowrap text-sm leading-tight text-gray-400">
          {tableType === 'viewer' && <TableViewerSVG />}
          {tableType === 'preview' && <TablePreviewSVG />}
          {tableType === 'viewer' && 'Viewer'}
          {tableType === 'preview' && 'Preview'}
          <span className="px-1.5 text-gray-300">• </span>
          <span className="truncate">
            Updated
            <time dateTime={dateTime} title={timeTitle}>
              {date}
            </time>
          </span>
          <span className="px-1.5 text-gray-300">• </span>
          <DownloadSVG />
          {downloads}
          <span className="px-1.5 text-gray-300">• </span>
          <FavoriteSVG />
          {favorites}
        </div>
      </a>
    </article>
  )
}