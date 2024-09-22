'use client'

import { NextPageSVG, PreviousPageSVG } from '@/ui/svgs'

export function DatasetsPagination({page, maxPage}: {page: number, maxPage: number}) {
  //linter TODO remove line
  console.log(maxPage)

  return (
    <nav>
      <ul className="flex select-none items-center justify-between space-x-2 text-gray-700 sm:justify-center mt-10 mx-auto">
        <li>
          <a
            // className="flex items-center rounded-lg px-2.5 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 pointer-events-none cursor-default text-gray-400 hover:text-gray-700"
            className="flex items-center rounded-lg px-2.5 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 "
            href={page > 0 ? `?p=${page-2}` : ''}
          >
            <PreviousPageSVG />
            Previous
          </a>
        </li>
        <li className="hidden sm:block">
          <a
            className={`rounded-lg px-2.5 py-1 ${page==1 && 'bg-gray-50 font-semibold ring-1 ring-inset ring-gray-200 dark:bg-gray-900 dark:text-yellow-500 dark:ring-gray-900'} hover:bg-gray-50 dark:hover:bg-gray-800`}
            href="?p=0"
          >
            1
          </a>
        </li>
        <li className="hidden sm:block">
          <a className={`rounded-lg px-2.5 py-1 ${page==2 && 'bg-gray-50 font-semibold ring-1 ring-inset ring-gray-200 dark:bg-gray-900 dark:text-yellow-500 dark:ring-gray-900'}  hover:bg-gray-50 dark:hover:bg-gray-800`}
          href="?p=1">
            2
          </a>
        </li>
        <li className="hidden sm:block">
          <a className={`rounded-lg px-2.5 py-1 ${page==3 && 'bg-gray-50 font-semibold ring-1 ring-inset ring-gray-200 dark:bg-gray-900 dark:text-yellow-500 dark:ring-gray-900'}  hover:bg-gray-50 dark:hover:bg-gray-800`} href="?p=2">
            3
          </a>
        </li>
        {/* <li className="hidden sm:block">
          <a className="rounded-lg px-2.5 py-1  pointer-events-none cursor-default" href="#">
            ...
          </a>
        </li>
        <li className="hidden sm:block">
          <a
            className="rounded-lg px-2.5 py-1  hover:bg-gray-50 dark:hover:bg-gray-800"
            href="?p=1647&amp;sort=trending"
          >
            1,648
          </a>
        </li> */}
        <li>
          <a
            className="flex items-center rounded-lg px-2.5 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 "
            href={page < 2 ? `?p=${page}` : ''}
          >
            Next
            <NextPageSVG />
          </a>
        </li>
      </ul>
    </nav>
  )
}