import { InnerSearchSVG } from '@/ui/svgs'

export default function FilterTab() {
  return (
    <div className="mb-4 flex items-center justify-between lg:mr-8">
      <div className="relative flex min-w-0 flex-1 items-center">
        <InnerSearchSVG />
        <input
          className="h-7 min-w-0 flex-1 rounded-full border border-gray-200/70 bg-white pl-7 text-sm placeholder-gray-400 ring-0 focus:outline-none"
          autoComplete="off"
          placeholder="Filter Tasks by name"
          type="text"
          value=""
          readOnly
        />
      </div>
    </div>
  )
}
