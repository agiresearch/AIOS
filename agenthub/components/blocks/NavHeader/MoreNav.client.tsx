// import { useState } from 'react'
import { AppNavItemType, AppNavList } from './constant'

interface MoreNavInfoItem {
  name: AppNavItemType
  titleColor: string
}

export default function MoreNav() {
  // const [a, setA] = useState(false)
  const MoreNavInfoList: MoreNavInfoItem[] = [
    { name: 'Website', titleColor: 'blue' },
    { name: 'Community', titleColor: 'yellow' },
  ]

  return (
    <div className="absolute right-0 top-full z-10 !mt-3 mt-1 !w-52 w-auto min-w-0 max-w-xs overflow-hidden rounded-xl border border-gray-100 bg-white shadow-lg">
      <ul className="min-w-full">
        {MoreNavInfoList.map((navInfo, index) => (
          <li key={index}>
            <div
              className={`dark:to-gray-925 col-span-full flex items-center justify-between whitespace-nowrap bg-gradient-to-r from-${navInfo.titleColor}-50 to-white px-4 py-0.5 font-semibold text-${navInfo.titleColor}-800 dark:from-${navInfo.titleColor}-900 dark:text-${navInfo.titleColor}-100`}
            >
              {navInfo.name}
            </div>
            <ul>
              {AppNavList.filter((appNav) => appNav.type === navInfo.name).map((appNav, index) => (
                <li key={`fjdkfdf-${index}`}>
                  <a
                    className="flex cursor-pointer items-center whitespace-nowrap px-3 py-1.5 hover:bg-gray-50 hover:underline  dark:hover:bg-gray-800"
                    href={appNav.href}
                    target={appNav.target || '_self'}
                  >
                    {appNav.renderSVG && appNav.renderSVG()}
                    {appNav.name}
                  </a>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  )
}