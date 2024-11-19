import LeftTabsLayout from './TabsLayout/index.client'

export default function Datasets() {
  return (
    <div className="flex min-h-[calc(100vh_-_64px)]">
      <div className="container relative flex flex-col lg:grid lg:space-y-0 w-full lg:grid-cols-10 md:flex-1 md:grid-rows-full md:gap-6">
        <LeftTabsLayout />
      </div>
    </div>
  )
}
