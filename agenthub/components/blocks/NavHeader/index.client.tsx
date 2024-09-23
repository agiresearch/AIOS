'use client'

import { useEffect, useState } from 'react'
// import MoreNav from './MoreNav.client'
import SearchBar from './SearchBar.client'
import { AppNavList } from './constant'
import AllNavInSmallScreen from './AllNavInSmallScreen.client'

export default function NavHeader() {
  const [isSearchBarShow, setIsSearchBarShow] = useState<boolean>(false)
  // const [isMoreNavShow, setIsMoreNavShow] = useState<boolean>(false)
  const [isAllNavInSmallScreenShow, setIsAllNavInSmallScreenShow] = useState<boolean>(false)

  useEffect(() => {
    const handleResize = () => {
      setIsAllNavInSmallScreenShow(false)
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <div className="SVELTE_HYDRATER contents" data-props='{"isWide":false,"isZh":true}' data-target="MainHeader">
      <header className="border-b border-gray-100 py-3 items-center flex">
        <div className="container flex h-16 w-full items-center px-4">
          <div className="flex items-center pr-4 flex-1">
            <a className="mr-5 flex flex-none items-center lg:mr-6" href="/">
              <img
                alt="Hugging Face's logo"
                className="w-10 md:mr-2 rounded-full"
                src="https://chat.aios.foundation/_next/image?url=https%3A%2F%2Favatars.githubusercontent.com%2Fu%2F130198651%3Fv%3D4&w=1080&q=75"
              />
              <span className="hidden whitespace-nowrap text-lg font-bold md:block">Nexus</span>
            </a>
            <div className="relative mr-2 flex-1 sm:mr-4 lg:mr-6 lg:max-w-sm">
              <input
                autoComplete="off"
                className="form-input-alt h-9 w-full pl-8 pr-3 focus:shadow-xl dark:bg-gray-950"
                name=""
                onClick={() => {
                  setIsSearchBarShow(true)
                }}
                onBlur={() => {
                  setIsSearchBarShow(false)
                }}
                placeholder="Search models, datasets, users..."
                spellCheck="false"
                type="text"
              />
              <svg
                className="absolute left-2.5 top-1/2 -translate-y-1/2 transform text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                xmlnsXlink="http://www.w3.org/1999/xlink"
                aria-hidden="true"
                focusable="false"
                role="img"
                width="1em"
                height="1em"
                preserveAspectRatio="xMidYMid meet"
                viewBox="0 0 32 32"
              >
                <path
                  d="M30 28.59L22.45 21A11 11 0 1 0 21 22.45L28.59 30zM5 14a9 9 0 1 1 9 9a9 9 0 0 1-9-9z"
                  fill="currentColor"
                ></path>
              </svg>
              {isSearchBarShow && <SearchBar />}
            </div>
            <div className="flex flex-none items-center justify-center place-self-stretch p-0.5 lg:hidden">
              <button
                className="relative z-30 flex h-6 w-8 items-center justify-center"
                type="button"
                onClick={() => {
                  setIsAllNavInSmallScreenShow(!isAllNavInSmallScreenShow)
                }}
              >
                {!isAllNavInSmallScreenShow && (
                  <svg
                    width="1em"
                    height="1em"
                    viewBox="0 0 10 10"
                    className="text-xl"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    preserveAspectRatio="xMidYMid meet"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M1.65039 2.9999C1.65039 2.8066 1.80709 2.6499 2.00039 2.6499H8.00039C8.19369 2.6499 8.35039 2.8066 8.35039 2.9999C8.35039 3.1932 8.19369 3.3499 8.00039 3.3499H2.00039C1.80709 3.3499 1.65039 3.1932 1.65039 2.9999ZM1.65039 4.9999C1.65039 4.8066 1.80709 4.6499 2.00039 4.6499H8.00039C8.19369 4.6499 8.35039 4.8066 8.35039 4.9999C8.35039 5.1932 8.19369 5.3499 8.00039 5.3499H2.00039C1.80709 5.3499 1.65039 5.1932 1.65039 4.9999ZM2.00039 6.6499C1.80709 6.6499 1.65039 6.8066 1.65039 6.9999C1.65039 7.1932 1.80709 7.3499 2.00039 7.3499H8.00039C8.19369 7.3499 8.35039 7.1932 8.35039 6.9999C8.35039 6.8066 8.19369 6.6499 8.00039 6.6499H2.00039Z"
                    ></path>
                  </svg>
                )}
                {isAllNavInSmallScreenShow && (
                  <svg
                    className="text-xl"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1.1em"
                    height="1.1em"
                    preserveAspectRatio="xMidYMid meet"
                    viewBox="0 0 32 32"
                  >
                    <path
                      d="M24 9.4L22.6 8L16 14.6L9.4 8L8 9.4l6.6 6.6L8 22.6L9.4 24l6.6-6.6l6.6 6.6l1.4-1.4l-6.6-6.6L24 9.4z"
                      fill="currentColor"
                    ></path>
                  </svg>
                )}
              </button>
              {isAllNavInSmallScreenShow && <AllNavInSmallScreen />}
            </div>
          
          </div>
          <nav aria-label="Main" className="ml-auto hidden lg:flex flex-1">
            <ul className="flex items-center space-x-2">
              {AppNavList.filter((appNav) => appNav.type === 'App').map((appNav, index) => {
                return (
                  <li key={index}>
                    <a
                      className="group flex items-center px-2 py-0.5 hover:text-indigo-700 dark:hover:text-gray-400"
                      href={appNav.href}
                      target={appNav.target || '_self'}
                    >
                      {appNav.renderSVG && appNav.renderSVG()}
                      {appNav.name}
                    </a>
                  </li>
                )
              })}
              <div className='flex flex-grow h-full w-auto' />
             
            </ul>
          </nav>
        </div>
      </header>
    </div>
  )
}