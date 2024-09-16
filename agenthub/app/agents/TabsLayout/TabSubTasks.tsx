import { DatasetSubTasks } from '../const'

export default function TabSubTasks() {
  return (
    <>
      <div className="mb-3">
        <div className="flex flex-wrap">
          {DatasetSubTasks.map((name, index) => (
            <a key={index} className="tag tag-purple" href={`/datasets?task_ids=task_ids%3A${name}`}>
              <span>{name}</span>
            </a>
          ))}
        </div>
      </div>
    </>
  )
}
