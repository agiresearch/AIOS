'use client'

// import { useState } from 'react'

export default function AllNavInSmallScreen() {
  // const [a, setA] = useState(false)
  return (
    <div className="fixed inset-0 top-16 z-20 overflow-y-auto overscroll-contain bg-white">
      <nav aria-label="Main">
        <ul className="space-y-4 px-2 pb-4">
          <li className="space-y-2.5">
            <div className="dark:via-gray-925 dark:to-gray-925 -mx-2 flex h-7 items-center bg-gradient-to-r from-purple-50 to-white px-2 font-semibold text-purple-800 dark:from-purple-900 dark:text-gray-200">
              Account
            </div>
            <ul className="grid grid-cols-2 content-start gap-2.5">
              <li className="col-span-2 flex items-center p-2">
                <img
                  className="mr-3 h-10 w-10 flex-none overflow-hidden rounded-full"
                  src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/noauth/ixdrkZU00TY737tBSZzvK.jpeg?w=200&amp;h=200&amp;f=face"
                  alt=""
                />
                <a className="group leading-tight" href="/hylerrix">
                  <div className="text-xs text-gray-500">Profile</div>{' '}
                  <div className="group-hover:underline">hylerrix</div>
                </a>
                <a
                  href="/notifications"
                  className="group ml-auto block rounded-xl border border-gray-100 bg-gradient-to-r from-gray-50 to-gray-50 px-3 py-1.5 text-right leading-tight hover:from-gray-100/50 hover:to-gray-50 dark:border-gray-900 dark:from-gray-800 dark:to-gray-800"
                >
                  <p className="text-xs text-gray-500">
                    <span className="mr-1.5 inline-block h-1.5 w-1.5 translate-y-[-2px] rounded-full bg-gradient-to-b from-yellow-500 to-orange-500 brightness-150 grayscale"></span>
                    Notifications
                  </p>
                  <p className="group-hover:underline">Inbox (0)</p>
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/new">
                  New Model
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/new-dataset">
                  New Dataset
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/new-space">
                  New Space
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/organizations/new">
                  New Organization
                </a>
              </li>
              <li>
                <a className="btn w-full" href="https://ui.autotrain.huggingface.co/projects" target="__blank">
                  New AutoTrain Project
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/settings/profile">
                  Settings
                </a>
              </li>
              <li>
                <form action="/logout" method="post">
                  <input
                    type="hidden"
                    name="csrf"
                    value="eyJkYXRhIjp7ImV4cGlyYXRpb24iOjE2ODk5NjA1OTA4ODUsInVzZXJJZCI6IjY0YTJlMjhjZDA3ZDhhZWJiN2VlNjMxMiJ9LCJzaWduYXR1cmUiOiI5OTQyOGI4N2ZiNWJiMWQ1NjJlMzY0ZDZjYmYzZmUwMzI0MmE5MzM0OWYzYWExMmM1NGUzNjU0ZTZhYmIwZTBjIn0="
                  />
                  <button className="btn w-full" type="submit">
                    Sign Out
                  </button>
                </form>
              </li>
            </ul>
          </li>
          <li className="space-y-2.5">
            <div className="dark:via-gray-925 dark:to-gray-925 -mx-2 flex h-7 items-center bg-gradient-to-r from-blue-50 to-white px-2 font-semibold text-blue-800 dark:from-blue-900 dark:text-gray-200">
              Website
            </div>
            <ul className="grid grid-cols-2 content-start gap-2.5">
              <li>
                <a className="btn w-full" href="/models">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1em"
                    height="1em"
                    preserveAspectRatio="xMidYMid meet"
                    viewBox="0 0 24 24"
                  >
                    <path
                      className="uim-quaternary"
                      d="M20.23 7.24L12 12L3.77 7.24a1.98 1.98 0 0 1 .7-.71L11 2.76c.62-.35 1.38-.35 2 0l6.53 3.77c.29.173.531.418.7.71z"
                      opacity=".25"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-tertiary"
                      d="M12 12v9.5a2.09 2.09 0 0 1-.91-.21L4.5 17.48a2.003 2.003 0 0 1-1-1.73v-7.5a2.06 2.06 0 0 1 .27-1.01L12 12z"
                      opacity=".5"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-primary"
                      d="M20.5 8.25v7.5a2.003 2.003 0 0 1-1 1.73l-6.62 3.82c-.275.13-.576.198-.88.2V12l8.23-4.76c.175.308.268.656.27 1.01z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  Models
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/datasets">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1em"
                    height="1em"
                    preserveAspectRatio="xMidYMid meet"
                    viewBox="0 0 25 25"
                  >
                    <ellipse cx="12.5" cy="5" fill="currentColor" fillOpacity="0.25" rx="7.5" ry="2"></ellipse>
                    <path
                      d="M12.5 15C16.6421 15 20 14.1046 20 13V20C20 21.1046 16.6421 22 12.5 22C8.35786 22 5 21.1046 5 20V13C5 14.1046 8.35786 15 12.5 15Z"
                      fill="currentColor"
                      opacity="0.5"
                    ></path>
                    <path
                      d="M12.5 7C16.6421 7 20 6.10457 20 5V11.5C20 12.6046 16.6421 13.5 12.5 13.5C8.35786 13.5 5 12.6046 5 11.5V5C5 6.10457 8.35786 7 12.5 7Z"
                      fill="currentColor"
                      opacity="0.5"
                    ></path>
                    <path
                      d="M5.23628 12C5.08204 12.1598 5 12.8273 5 13C5 14.1046 8.35786 15 12.5 15C16.6421 15 20 14.1046 20 13C20 12.8273 19.918 12.1598 19.7637 12C18.9311 12.8626 15.9947 13.5 12.5 13.5C9.0053 13.5 6.06886 12.8626 5.23628 12Z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  Datasets
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/tasks">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    role="img"
                    width="1em"
                    height="1em"
                    preserveAspectRatio="xMidYMid meet"
                    viewBox="0 0 24 24"
                  >
                    <path
                      className="uim-tertiary"
                      d="M15.273 18.728A6.728 6.728 0 1 1 22 11.999V12a6.735 6.735 0 0 1-6.727 6.728z"
                      opacity=".5"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-primary"
                      d="M8.727 18.728A6.728 6.728 0 1 1 15.455 12a6.735 6.735 0 0 1-6.728 6.728z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  Tasks
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/papers">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1em"
                    height="1em"
                    viewBox="0 0 12 12"
                    preserveAspectRatio="xMidYMid meet"
                    fill="none"
                  >
                    <path
                      fill="currentColor"
                      fill-rule="evenodd"
                      d="M7.55 1.02c.29 0 .58.11.8.29l1.48 1.22c.3.25.45.6.45.97v6.22c0 .7-.56 1.26-1.25 1.26H2.97c-.7 0-1.26-.56-1.26-1.26V2.28c0-.7.56-1.26 1.26-1.26h4.57Zm.11 3.63c-.76 0-1.36-.6-1.36-1.36v-.7a.62.62 0 0 0-.63-.64h-2.7a.31.31 0 0 0-.31.33v7.44c0 .18.13.33.3.33h6.07c.18 0 .31-.15.31-.33V5.3a.62.62 0 0 0-.62-.64H7.65h.01Z"
                      clip-rule="evenodd"
                    ></path>
                  </svg>
                  Daily Papers
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/metrics">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1em"
                    height="1em"
                    preserveAspectRatio="xMidYMid meet"
                    viewBox="0 0 24 24"
                  >
                    <path
                      className="uim-quaternary"
                      d="M6 23H2a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1z"
                      opacity=".25"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-primary"
                      d="M14 23h-4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v20a1 1 0 0 1-1 1z"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-tertiary"
                      d="M22 23h-4a1 1 0 0 1-1-1V10a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1z"
                      opacity=".5"
                      fill="currentColor"
                    ></path>
                  </svg>
                  Metrics
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/languages">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1em"
                    height="1em"
                    preserveAspectRatio="xMidYMid meet"
                    viewBox="0 0 24 24"
                  >
                    <path
                      className="uim-primary"
                      d="M17 13H7a1 1 0 0 1 0-2h10a1 1 0 0 1 0 2z"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-tertiary"
                      d="M12 2a10 10 0 0 0-7.743 16.33l-1.964 1.963A1 1 0 0 0 3 22h9a10 10 0 0 0 0-20zM9 7h6a1 1 0 0 1 0 2H9a1 1 0 0 1 0-2zm6 10H9a1 1 0 0 1 0-2h6a1 1 0 0 1 0 2zm2-4H7a1 1 0 0 1 0-2h10a1 1 0 0 1 0 2z"
                      opacity=".5"
                      fill="currentColor"
                    ></path>
                    <path
                      className="uim-primary"
                      d="M15 17H9a1 1 0 0 1 0-2h6a1 1 0 0 1 0 2zm0-8H9a1 1 0 0 1 0-2h6a1 1 0 0 1 0 2z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  Languages
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/spaces">
                  <svg
                    className="mr-1.5 text-gray-400"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlnsXlink="http://www.w3.org/1999/xlink"
                    aria-hidden="true"
                    focusable="false"
                    role="img"
                    width="1em"
                    height="1em"
                    viewBox="0 0 25 25"
                  >
                    <path
                      opacity=".5"
                      d="M6.016 14.674v4.31h4.31v-4.31h-4.31ZM14.674 14.674v4.31h4.31v-4.31h-4.31ZM6.016 6.016v4.31h4.31v-4.31h-4.31Z"
                      fill="currentColor"
                    ></path>
                    <path
                      opacity=".75"
                      fill-rule="evenodd"
                      clip-rule="evenodd"
                      d="M3 4.914C3 3.857 3.857 3 4.914 3h6.514c.884 0 1.628.6 1.848 1.414a5.171 5.171 0 0 1 7.31 7.31c.815.22 1.414.964 1.414 1.848v6.514A1.914 1.914 0 0 1 20.086 22H4.914A1.914 1.914 0 0 1 3 20.086V4.914Zm3.016 1.102v4.31h4.31v-4.31h-4.31Zm0 12.968v-4.31h4.31v4.31h-4.31Zm8.658 0v-4.31h4.31v4.31h-4.31Zm0-10.813a2.155 2.155 0 1 1 4.31 0 2.155 2.155 0 0 1-4.31 0Z"
                      fill="currentColor"
                    ></path>
                    <path
                      opacity=".25"
                      d="M16.829 6.016a2.155 2.155 0 1 0 0 4.31 2.155 2.155 0 0 0 0-4.31Z"
                      fill="currentColor"
                    ></path>
                  </svg>
                  Spaces
                </a>
              </li>
            </ul>
          </li>
          <li className="space-y-2.5">
            <div className="dark:via-gray-925 dark:to-gray-925 -mx-2 flex h-7 items-center bg-gradient-to-r from-pink-50 to-white px-2 font-semibold text-pink-800 dark:from-pink-900 dark:text-gray-200">
              Solutions
            </div>
            <ul className="grid grid-cols-2 content-start gap-2.5">
              <li>
                <a className="btn w-full" href="/pricing">
                  Pricing
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/enterprise">
                  Enterprise Hub
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/support">
                  Expert Support
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/inference-endpoints">
                  Inference Endpoints
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/autotrain">
                  AutoTrain
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/hardware">
                  Hardware
                </a>
              </li>
            </ul>
          </li>
          <li className="space-y-2.5">
            <div className="dark:via-gray-925 dark:to-gray-925 -mx-2 flex h-7 items-center bg-gradient-to-r from-yellow-50 to-white px-2 font-semibold text-yellow-800 dark:from-yellow-900 dark:text-gray-200">
              Community
            </div>
            <ul className="grid grid-cols-2 content-start gap-2.5">
              <li>
                <a className="btn w-full" href="https://discuss.huggingface.co/" target="__blank">
                  Forum
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/blog/zh">
                  Blog
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/join/discord" target="__blank">
                  Discord
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/classrooms">
                  Classrooms
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/learn">
                  Learn
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/shop">
                  HF Store
                </a>
              </li>
            </ul>
          </li>
          <li className="space-y-2.5">
            <div className="dark:via-gray-925 dark:to-gray-925 -mx-2 flex h-7 items-center bg-gradient-to-r from-green-50 to-white px-2 font-semibold text-green-800 dark:from-green-900 dark:text-gray-200">
              Documentation
            </div>
            <ul className="grid grid-cols-2 content-start gap-2.5">
              <li>
                <a className="btn w-full" href="/docs">
                  Doc Search
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/hub">
                  Hub doc
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/accelerate/">
                  Accelerate doc
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/datasets/">
                  Datasets doc
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/api-inference/" target="__blank">
                  Inference API doc
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/sagemaker/">
                  SageMaker doc
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/tokenizers/python/latest/">
                  Tokenizers doc
                </a>
              </li>
              <li>
                <a className="btn w-full" href="/docs/transformers/">
                  Transformers doc
                </a>
              </li>
            </ul>
          </li>
        </ul>
      </nav>
    </div>
  )
}