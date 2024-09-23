import { DatasetOther } from '../const'

export default function TabOther() {
  return (
    <div className="mb-3">
      <div className="flex flex-wrap">
        {DatasetOther.map((item, index) => (
          <a key={index} className="tag  tag-white" href={`/datasets?other=${item}`}>
            <span>{item}</span>
          </a>
        ))}
      </div>
    </div>
  )
}
