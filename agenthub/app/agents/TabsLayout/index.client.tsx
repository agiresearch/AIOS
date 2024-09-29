'use client'

import { useState } from 'react'
import classNames from 'classnames'

import { DatasetsTabList } from '../const'
import { DatasetsTabItem } from '../type'

import FilterTab from './FilterTab'
import TabTasks from './TabTasks'
import TabOther from './TabOther'
import TabLicenses from './TabLicenses'
import TabLanguages from './TabLanguages'
import TabSubTasks from './TabSubTasks'
import TabSizes from './TabSizes'
import { ApplySVG, ExitSVG } from '@/ui/svgs'

export default function LeftTabsLayout() {
  const [currentTab, setCurrentTab] = useState<DatasetsTabItem>('Tasks')
  //linter
  // const [isAddFilterModalDisplay, setIsAddFilterModalDisplay] = useState<boolean>(false)
  const isAddFilterModalDisplay = false;

  const onTabClick = (tabName: DatasetsTabItem) => {
    setCurrentTab(tabName)
  }

  return (
    <section
      className={classNames(
        'pt-8 border-gray-100 bg-white lg:static lg:px-0 lg:col-span-4 xl:col-span-3 lg:border-r lg:bg-gradient-to-l from-gray-50-to-white',
        isAddFilterModalDisplay ? 'fixed overflow-y-auto overflow-x-hidden z-40 inset-0 !px-4 !pt-4' : 'hidden lg:block'
      )}
    >
      <div className="mb-4 flex items-center justify-between lg:hidden">
        <h3 className="text-base font-semibold">Edit Datasets filters</h3>
        <button className="text-xl" type="button">
          <ExitSVG />
        </button>
      </div>
      <ul className="flex gap-1 text-sm flex-wrap mt-1.5 mb-5">
        {DatasetsTabList.map((tabName, index) => (
          <li key={index}>
            <button
              className={classNames(
                'flex items-center whitespace-nowrap rounded-lg px-2',
                currentTab === tabName
                  ? 'bg-black text-white dark:bg-gray-800'
                  : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-900 dark:hover:text-gray-300'
              )}
              onClick={() => {
                onTabClick(tabName)
              }}
            >
              {tabName}
            </button>
          </li>
        ))}
      </ul>
      <FilterTab />
      <div className="mb-3">
        {currentTab === 'Tasks' && <TabTasks />}
        {currentTab === 'Sizes' && <TabSizes />}
        {currentTab === 'Sub-tasks' && <TabSubTasks />}
        {currentTab === 'Languages' && <TabLanguages />}
        {currentTab === 'Licenses' && <TabLicenses />}
        {currentTab === 'Other' && <TabOther />}
      </div>
      <div className="fixed inset-x-4 bottom-0 flex h-16 items-center border-t bg-white dark:bg-gray-950 lg:hidden">
        <button className="btn btn-lg -mt-px w-full font-semibold" type="button">
          <ApplySVG />
          Apply filters
        </button>
      </div>
    </section>
  )
}
