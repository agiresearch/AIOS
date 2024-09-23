export default function SearchBar() {
    return (
      <div className="absolute z-40 w-full md:min-w-[24rem]">
        <ul className="mt-1 max-h-[calc(100vh-100px)] w-full divide-y divide-gray-100 overflow-hidden overflow-y-auto rounded-lg border border-gray-100 bg-white text-sm shadow-lg dark:divide-gray-900 ">
          <li className="flex h-7 items-center bg-gradient-to-r from-blue-50 to-white px-2 font-semibold text-blue-800 dark:from-blue-900 dark:to-gray-950 dark:text-gray-300">
            Models
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center bg-blue-500 px-2 font-mono  text-xs text-white dark:bg-blue-700"
              href="/THUDM/chatglm2-6b"
            >
              <span className="truncate px-1">THUDM/chatglm2-6b</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/stabilityai/stable-diffusion-xl-base-0.9"
            >
              <span className="dark:from-gray-925 truncate rounded bg-gradient-to-b from-gray-50 to-gray-100 px-1 dark:to-gray-950">
                stabilityai/stable-diffusion-xl-base-0.9
              </span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/meta-llama/Llama-2-7b"
            >
              <span className="dark:from-gray-925 truncate rounded bg-gradient-to-b from-gray-50 to-gray-100 px-1 dark:to-gray-950">
                meta-llama/Llama-2-7b
              </span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/runwayml/stable-diffusion-v1-5"
            >
              <span className="dark:from-gray-925 truncate rounded bg-gradient-to-b from-gray-50 to-gray-100 px-1 dark:to-gray-950">
                runwayml/stable-diffusion-v1-5
              </span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/lllyasviel/ControlNet-v1-1"
            >
              <span className="dark:from-gray-925 truncate rounded bg-gradient-to-b from-gray-50 to-gray-100 px-1 dark:to-gray-950">
                lllyasviel/ControlNet-v1-1
              </span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/cerspense/zeroscope_v2_XL"
            >
              <span className="dark:from-gray-925 truncate rounded bg-gradient-to-b from-gray-50 to-gray-100 px-1 dark:to-gray-950">
                cerspense/zeroscope_v2_XL
              </span>
            </a>
          </li>
          <li className="flex h-7 items-center bg-gradient-to-r from-red-50 to-white px-2 font-semibold text-red-800 dark:from-red-900 dark:to-gray-950 dark:text-gray-300">
            Datasets
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/datasets/Open-Orca/OpenOrca"
            >
              <span className="truncate px-1">Open-Orca/OpenOrca</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/datasets/fka/awesome-chatgpt-prompts"
            >
              <span className="truncate px-1">fka/awesome-chatgpt-prompts</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/datasets/tiiuae/falcon-refinedweb"
            >
              <span className="truncate px-1">tiiuae/falcon-refinedweb</span>
            </a>
          </li>
          <li className="flex h-7 items-center bg-gradient-to-r from-orange-50 to-white px-2 font-semibold text-orange-800 dark:from-orange-900 dark:to-gray-950 dark:text-gray-300">
            Spaces
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/spaces/HuggingFaceH4/open_llm_leaderboard"
            >
              <span className="truncate px-1">HuggingFaceH4/open_llm_leaderboard</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/spaces/DragGan/DragGan"
            >
              <span className="truncate px-1">DragGan/DragGan</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2 font-mono text-xs  hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/spaces/huggingface-projects/QR-code-AI-art-generator"
            >
              <span className="truncate px-1">huggingface-projects/QR-code-AI-art-generator</span>
            </a>
          </li>
          <li className="flex h-7 items-center bg-gradient-to-r from-purple-50 to-white px-2 font-semibold text-indigo-800 dark:from-indigo-900 dark:to-gray-950 dark:text-gray-300">
            Organizations
          </li>
          <li>
            <a className="flex h-8 cursor-pointer items-center px-2   hover:bg-gray-50 dark:hover:bg-gray-900" href="/-1">
              <img
                alt=""
                className="mr-1.5 h-3.5 w-3.5 rounded"
                src="https://www.gravatar.com/avatar/6bb61e3b7bce0931da574d19d1d82c88?d=retro&amp;size=100"
              />
              <span className="truncate px-1">Subzero</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2   hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/0-2"
            >
              <img
                alt=""
                className="mr-1.5 h-3.5 w-3.5 rounded"
                src="https://www.gravatar.com/avatar/dfbffab08ce62ec457a6c2cf7f55e76c?d=retro&amp;size=100"
              />
              <span className="truncate px-1">Sub-one</span>
            </a>
          </li>
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2   hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/0-o"
            >
              <img
                alt=""
                className="mr-1.5 h-3.5 w-3.5 rounded"
                src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1671317055220-63177bcd212fce5a3cd42215.png?w=200&amp;h=200&amp;f=face"
              />
              <span className="truncate px-1">0-o</span>
            </a>
          </li>
        </ul>
        <ul className="mt-1 max-h-[calc(100vh-100px)] w-full divide-y divide-gray-100 overflow-hidden overflow-y-auto rounded-lg border border-gray-100 bg-white text-sm shadow-lg">
          <li>
            <a
              className="flex h-8 cursor-pointer items-center px-2   hover:bg-gray-50 dark:hover:bg-gray-900"
              href="/search/full-text"
            >
              <span className="mr-1.5 rounded bg-blue-500/10 px-1 text-xs leading-tight text-blue-700 dark:text-blue-200">
                new
              </span>
              <span className="truncate px-1">Try Full-text search </span>
              <svg
                className="ml-auto h-3.5 w-3.5 flex-none"
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
                <path d="M18 6l-1.4 1.4l7.5 7.6H3v2h21.1l-7.5 7.6L18 26l10-10z" fill="currentColor"></path>
              </svg>
            </a>
          </li>
        </ul>
      </div>
    )
  }