export default function LandingPageMain() {
    return (
      <main className="flex flex-1 flex-col">
        <div className="flex-1">
          <div className="container pb-32 pt-28 text-center 2xl:pb-40 2xl:pt-32">
            <div className="mx-auto -mt-16 mb-12 flex items-center justify-center">
              <div className="text-smd flex flex-wrap items-center rounded-lg bg-indigo-50 p-2 text-indigo-900 max-sm:justify-center sm:py-1 md:rounded-full">
                <div className="mr-2 rounded-lg bg-indigo-200 px-1.5 text-xs font-semibold text-indigo-700 max-sm:mb-1.5">
                  NEW
                </div>
                <p>
                  Deploy
                  <a href="/meta-llama" className="font-semibold">
                    LLama 2
                  </a>
                  (
                  <a
                    className="underline decoration-indigo-200 hover:decoration-indigo-700"
                    href="https://ui.endpoints.huggingface.co/new?repository=meta-llama%2FLlama-2-7b-chat-hf"
                  >
                    Chat 7B
                  </a>
                  and
                  <a
                    className="underline decoration-indigo-200 hover:decoration-indigo-700"
                    href="https://ui.endpoints.huggingface.co/new?repository=meta-llama%2FLlama-2-13b-chat-hf"
                  >
                    13B
                  </a>
                  ) in a few clicks on
                  <svg
                    className="ml-0.5 inline -translate-y-px"
                    width="1em"
                    height="1em"
                    viewBox="0 0 74 75"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M46.6517 14.9309C48.2799 11.0495 45.4292 6.76251 41.2202 6.76251H24.1817C19.8066 6.76251 15.9021 9.50789 14.4218 13.6249L8.51785 30.0453C6.77792 34.8844 6.77792 40.1785 8.51785 45.0177L14.4218 61.438C15.9021 65.5551 19.8066 68.3004 24.1817 68.3004H41.2202C45.4292 68.3004 48.2799 64.0134 46.6517 60.132L40.7616 46.0903C38.465 40.6155 38.465 34.4475 40.7616 28.9727L46.6517 14.9309Z"
                      fill="#861FFF"
                      stroke="black"
                      strokeWidth="12.6835"
                      strokeLinejoin="round"
                    ></path>
                    <circle
                      cx="53.1334"
                      cy="37.5315"
                      r="13.9518"
                      fill="#FF3270"
                      stroke="black"
                      strokeWidth="12.6835"
                      strokeLinejoin="round"
                    ></circle>
                  </svg>
                  <a href="/inference-endpoints" className="underline decoration-indigo-200 hover:decoration-indigo-700">
                    Inference Endpoints
                  </a>
                </p>
              </div>
            </div>
            <img className="mx-auto mb-4 h-24 w-24" src="/front/assets/huggingface_logo-noborder.svg" alt="" />
            <h1 className="mx-auto max-w-xl text-4xl font-bold text-gray-900 dark:text-gray-100 md:text-6xl">
              The AI community building the future.
            </h1>
            <p className="mx-auto mt-6 max-w-md text-lg text-gray-500">
              Build, train and deploy state of the art models powered by the reference open source in machine learning.
            </p>
            <div className="mt-12 flex items-center justify-center">
              <a href="https://github.com/huggingface/transformers" className="btn -mr-1 text-lg font-bold">
                <svg
                  className="mr-2 dark:text-gray-200"
                  xmlns="http://www.w3.org/2000/svg"
                  xmlnsXlink="http://www.w3.org/1999/xlink"
                  aria-hidden="true"
                  focusable="false"
                  role="img"
                  width="1.03em"
                  height="1em"
                  preserveAspectRatio="xMidYMid meet"
                  viewBox="0 0 256 250"
                >
                  <path
                    d="M128.001 0C57.317 0 0 57.307 0 128.001c0 56.554 36.676 104.535 87.535 121.46c6.397 1.185 8.746-2.777 8.746-6.158c0-3.052-.12-13.135-.174-23.83c-35.61 7.742-43.124-15.103-43.124-15.103c-5.823-14.795-14.213-18.73-14.213-18.73c-11.613-7.944.876-7.78.876-7.78c12.853.902 19.621 13.19 19.621 13.19c11.417 19.568 29.945 13.911 37.249 10.64c1.149-8.272 4.466-13.92 8.127-17.116c-28.431-3.236-58.318-14.212-58.318-63.258c0-13.975 5-25.394 13.188-34.358c-1.329-3.224-5.71-16.242 1.24-33.874c0 0 10.749-3.44 35.21 13.121c10.21-2.836 21.16-4.258 32.038-4.307c10.878.049 21.837 1.47 32.066 4.307c24.431-16.56 35.165-13.12 35.165-13.12c6.967 17.63 2.584 30.65 1.255 33.873c8.207 8.964 13.173 20.383 13.173 34.358c0 49.163-29.944 59.988-58.447 63.157c4.591 3.972 8.682 11.762 8.682 23.704c0 17.126-.148 30.91-.148 35.126c0 3.407 2.304 7.398 8.792 6.14C219.37 232.5 256 184.537 256 128.002C256 57.307 198.691 0 128.001 0zm-80.06 182.34c-.282.636-1.283.827-2.194.39c-.929-.417-1.45-1.284-1.15-1.922c.276-.655 1.279-.838 2.205-.399c.93.418 1.46 1.293 1.139 1.931zm6.296 5.618c-.61.566-1.804.303-2.614-.591c-.837-.892-.994-2.086-.375-2.66c.63-.566 1.787-.301 2.626.591c.838.903 1 2.088.363 2.66zm4.32 7.188c-.785.545-2.067.034-2.86-1.104c-.784-1.138-.784-2.503.017-3.05c.795-.547 2.058-.055 2.861 1.075c.782 1.157.782 2.522-.019 3.08zm7.304 8.325c-.701.774-2.196.566-3.29-.49c-1.119-1.032-1.43-2.496-.726-3.27c.71-.776 2.213-.558 3.315.49c1.11 1.03 1.45 2.505.701 3.27zm9.442 2.81c-.31 1.003-1.75 1.459-3.199 1.033c-1.448-.439-2.395-1.613-2.103-2.626c.301-1.01 1.747-1.484 3.207-1.028c1.446.436 2.396 1.602 2.095 2.622zm10.744 1.193c.036 1.055-1.193 1.93-2.715 1.95c-1.53.034-2.769-.82-2.786-1.86c0-1.065 1.202-1.932 2.733-1.958c1.522-.03 2.768.818 2.768 1.868zm10.555-.405c.182 1.03-.875 2.088-2.387 2.37c-1.485.271-2.861-.365-3.05-1.386c-.184-1.056.893-2.114 2.376-2.387c1.514-.263 2.868.356 3.061 1.403z"
                    fill="currentColor"
                  ></path>
                </svg>
                Star
              </a>
              <div className="relative ml-3">
                <div className="from-gray-100-to-white dark:border-gray-850 absolute -left-1 top-3.5 z-[-1] h-3 w-3 flex-none rotate-45 rounded-sm border border-gray-200 bg-gradient-to-t dark:bg-gray-900"></div>
                <a
                  className="btn inset-0 text-lg font-bold dark:hover:text-yellow-500"
                  href="https://github.com/huggingface/transformers"
                >
                  108,050
                </a>
              </div>
            </div>
          </div>
          <div className="mx-auto max-w-5xl px-4 pb-16 text-center 2xl:max-w-6xl">
            <div className="rounded-lg-b rounded-lg-gray-200 -mb-3.5 border border-gray-100"></div>
            <div className="font-sm mb-6 inline-block bg-white px-4 text-gray-500">
              More than 5,000 organizations are using Hugging Face
            </div>
            <div className="grid gap-3 text-left md:grid-cols-2 lg:grid-cols-4">
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/allenai">
                  <img
                    alt="Allen Institute for AI's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1584460628617-5e70f0eb8ce3c604d78fe130.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Allen Institute for AI">
                      <span className="truncate">Allen Institute for AI</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">non-profit</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>
                      193 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/facebook">
                  <img
                    alt="Meta AI's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1592839207516-noauth.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Meta AI">
                      <span className="truncate">Meta AI</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">company</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>
                      700 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/amazon">
                  <img
                    alt="Amazon Web Services's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1625068211554-5e67de201009063689407481.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Amazon Web Services">
                      <span className="truncate">Amazon Web Services</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">company</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>2 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/google">
                  <img
                    alt="Google's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/5dd96eb166059660ed1ee413/WtA3YYitedOr9n02eHfJe.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Google">
                      <span className="truncate">Google</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">company</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>
                      593 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/Intel">
                  <img
                    alt="Intel's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1616186257611-60104afcc75e19ac1738fe70.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Intel">
                      <span className="truncate">Intel</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">company</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>
                      131 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/speechbrain">
                  <img
                    alt="SpeechBrain's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1663000279893-60243f18c1f3c79f98e4b382.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="SpeechBrain">
                      <span className="truncate">SpeechBrain</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">non-profit</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>
                      76 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/microsoft">
                  <img
                    alt="Microsoft's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1583646260758-5e64858c87403103f9f1055d.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Microsoft">
                      <span className="truncate">Microsoft</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">company</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>
                      257 models
                    </div>
                  </div>
                </a>
              </article>
              <article className="overview-card-wrapper ">
                <a className="flex flex-1 items-center overflow-hidden p-2" href="/grammarly">
                  <img
                    alt="Grammarly's profile picture"
                    className="mr-3 h-8 w-8 flex-none rounded-lg"
                    src="https://aeiljuispo.cloudimg.io/v7/https://cdn-uploads.huggingface.co/production/uploads/1611152856266-5dd96eb166059660ed1ee413.png?w=200&amp;h=200&amp;f=face"
                  />
                  <div className="overflow-hidden leading-tight">
                    <h4 className="flex items-center font-semibold " title="Grammarly">
                      <span className="truncate">Grammarly</span>
                    </h4>
                    <div className="truncate text-sm leading-tight text-gray-400">
                      <span className="capitalize">company</span>
                      <span className="px-0.5 text-xs text-gray-300">•</span>6 models
                    </div>
                  </div>
                </a>
              </article>
            </div>
          </div>
        </div>
        <div className="overflow-hidden bg-gradient-to-b from-white via-red-200/20 to-indigo-200/20 pt-14 dark:from-gray-950 dark:to-gray-900">
          <div className="container grid gap-x-6 gap-y-12 lg:grid-cols-3 lg:gap-y-0">
            <div className="lg:-mt-6 lg:self-center lg:pr-12">
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <svg
                      className="text-xl text-orange-400"
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
                    <div className="h-2"></div>
                    <p className="font-mono text-sm text-gray-500">Hub</p>
                    <h2 className="false text-2xl font-semibold leading-tight text-gray-800">Home of Machine Learning</h2>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="max-w-sm leading-snug text-gray-500">
                  Create, discover and collaborate on ML better.
                  <br />
                  Join the community to start your ML journey.
                </p>
                <div className="h-6"></div>
                <a
                  href="/join"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Sign Up
                </a>
              </div>
            </div>
            <div className="relative lg:col-span-2">
              <img
                className="relative -mb-px hidden overflow-hidden rounded-t-xl border border-b-0 border-gray-100 bg-white md:block"
                style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                src="/front/assets/activity-feed.png"
                alt="Hugging Face Hub dashboard"
              />
              <img
                className="relative -mb-px overflow-hidden rounded-t-xl border border-b-0 border-gray-100 bg-white md:hidden"
                style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                src="/front/assets/activity-feed-mobile.png"
                alt="Hugging Face Hub dashboard"
              />
            </div>
          </div>
        </div>
        <div className="max-w-full overflow-hidden border-y border-gray-100 bg-gradient-to-br py-24 dark:from-gray-950 dark:to-gray-900 md:py-32">
          <div className="container grid grid-cols-1 gap-y-12 md:grid-cols-4 md:gap-y-0">
            <div className="pr-12 md:col-span-1">
              <div className="flex flex-col">
                <svg
                  className="text-xl text-green-400"
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
                <div className="h-2"></div>
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">Tasks</p>
                    <h2 className="false text-2xl font-semibold leading-tight text-gray-800">Problems solvers</h2>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  Thousands of creators work as a community to solve Audio, Vision, and Language with AI.
                </p>
                <div className="h-6"></div>
                <a
                  href="/tasks"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Explore tasks
                </a>
              </div>
            </div>
            <div className="relative ml-auto flex space-x-3 bg-gradient-to-b from-white via-purple-100/40 to-white md:col-span-3">
              <div className="-ml-16 flex space-x-2 md:-ml-0">
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/audio-classification"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-green-400"
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
                        d="M25 4H10a2.002 2.002 0 0 0-2 2v14.556A3.955 3.955 0 0 0 6 20a4 4 0 1 0 4 4V12h15v8.556A3.954 3.954 0 0 0 23 20a4 4 0 1 0 4 4V6a2.002 2.002 0 0 0-2-2zM6 26a2 2 0 1 1 2-2a2.002 2.002 0 0 1-2 2zm17 0a2 2 0 1 1 2-2a2.003 2.003 0 0 1-2 2zM10 6h15v4H10z"
                        fill="currentColor"
                      ></path>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Audio Classification</header>
                    <p className="text-sm text-gray-400">770 models</p>
                  </a>
                </div>
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/image-classification"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-blue-400"
                      xmlns="http://www.w3.org/2000/svg"
                      xmlnsXlink="http://www.w3.org/1999/xlink"
                      aria-hidden="true"
                      fill="currentColor"
                      focusable="false"
                      role="img"
                      width="1em"
                      height="1em"
                      preserveAspectRatio="xMidYMid meet"
                      viewBox="0 0 32 32"
                    >
                      <polygon points="4 20 4 22 8.586 22 2 28.586 3.414 30 10 23.414 10 28 12 28 12 20 4 20"></polygon>
                      <path d="M19,14a3,3,0,1,0-3-3A3,3,0,0,0,19,14Zm0-4a1,1,0,1,1-1,1A1,1,0,0,1,19,10Z"></path>
                      <path d="M26,4H6A2,2,0,0,0,4,6V16H6V6H26V21.17l-3.59-3.59a2,2,0,0,0-2.82,0L18,19.17,11.8308,13l-1.4151,1.4155L14,18l2.59,2.59a2,2,0,0,0,2.82,0L21,19l5,5v2H16v2H26a2,2,0,0,0,2-2V6A2,2,0,0,0,26,4Z"></path>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Image Classification</header>
                    <p className="text-sm text-gray-400">4,493 models</p>
                  </a>
                </div>
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/object-detection"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-yellow-400"
                      xmlns="http://www.w3.org/2000/svg"
                      xmlnsXlink="http://www.w3.org/1999/xlink"
                      aria-hidden="true"
                      fill="currentColor"
                      focusable="false"
                      role="img"
                      width="1em"
                      height="1em"
                      preserveAspectRatio="xMidYMid meet"
                      viewBox="0 0 32 32"
                    >
                      <path d="M24,14a5.99,5.99,0,0,0-4.885,9.4712L14,28.5859,15.4141,30l5.1147-5.1147A5.9971,5.9971,0,1,0,24,14Zm0,10a4,4,0,1,1,4-4A4.0045,4.0045,0,0,1,24,24Z"></path>
                      <path d="M17,12a3,3,0,1,0-3-3A3.0033,3.0033,0,0,0,17,12Zm0-4a1,1,0,1,1-1,1A1.0009,1.0009,0,0,1,17,8Z"></path>
                      <path d="M12,24H4V17.9966L9,13l5.5859,5.5859L16,17.168l-5.5859-5.5855a2,2,0,0,0-2.8282,0L4,15.168V4H24v6h2V4a2.0023,2.0023,0,0,0-2-2H4A2.002,2.002,0,0,0,2,4V24a2.0023,2.0023,0,0,0,2,2h8Z"></path>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Object Detection</header>
                    <p className="text-sm text-gray-400">536 models</p>
                  </a>
                </div>
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/question-answering"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-blue-400"
                      xmlns="http://www.w3.org/2000/svg"
                      xmlnsXlink="http://www.w3.org/1999/xlink"
                      width="1em"
                      height="1em"
                      preserveAspectRatio="xMidYMid meet"
                      viewBox="0 0 32 32"
                    >
                      <path d="M2 9h9V2H2zm2-5h5v3H4z" fill="currentColor"></path>
                      <path d="M2 19h9v-7H2zm2-5h5v3H4z" fill="currentColor"></path>
                      <path d="M2 29h9v-7H2zm2-5h5v3H4z" fill="currentColor"></path>
                      <path
                        d="M27 9h-9l3.41-3.59L20 4l-6 6l6 6l1.41-1.41L18 11h9a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H15v2h12a3 3 0 0 0 3-3V12a3 3 0 0 0-3-3z"
                        fill="currentColor"
                      ></path>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Question Answering</header>
                    <p className="text-sm text-gray-400">5,521 models</p>
                  </a>
                </div>
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/summarization"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-indigo-400"
                      xmlns="http://www.w3.org/2000/svg"
                      xmlnsXlink="http://www.w3.org/1999/xlink"
                      aria-hidden="true"
                      fill="currentColor"
                      focusable="false"
                      role="img"
                      width="1em"
                      height="1em"
                      preserveAspectRatio="xMidYMid meet"
                      viewBox="0 0 18 19"
                    >
                      <path d="M15.4988 8.79309L12.1819 5.47621C12.0188 5.25871 11.7469 5.14996 11.475 5.14996H7.12501C6.52688 5.14996 6.03751 5.63934 6.03751 6.23746V16.025C6.03751 16.6231 6.52688 17.1125 7.12501 17.1125H14.7375C15.3356 17.1125 15.825 16.6231 15.825 16.025V9.55434C15.825 9.28246 15.7163 9.01059 15.4988 8.79309V8.79309ZM11.475 6.23746L14.6831 9.49996H11.475V6.23746ZM7.12501 16.025V6.23746H10.3875V9.49996C10.3875 10.0981 10.8769 10.5875 11.475 10.5875H14.7375V16.025H7.12501Z"></path>
                      <path d="M3.8625 10.5875H2.775V2.97498C2.775 2.37686 3.26438 1.88748 3.8625 1.88748H11.475V2.97498H3.8625V10.5875Z"></path>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Summarization</header>
                    <p className="text-sm text-gray-400">1,185 models</p>
                  </a>
                </div>
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/text-classification"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-orange-400"
                      xmlns="http://www.w3.org/2000/svg"
                      xmlnsXlink="http://www.w3.org/1999/xlink"
                      aria-hidden="true"
                      fill="currentColor"
                      focusable="false"
                      role="img"
                      width="1em"
                      height="1em"
                      preserveAspectRatio="xMidYMid meet"
                      viewBox="0 0 32 32"
                      style={{ transform: 'rotate(360deg)' }}
                    >
                      <circle cx="10" cy="20" r="2" fill="currentColor"></circle>
                      <circle cx="10" cy="28" r="2" fill="currentColor"></circle>
                      <circle cx="10" cy="14" r="2" fill="currentColor"></circle>
                      <circle cx="28" cy="4" r="2" fill="currentColor"></circle>
                      <circle cx="22" cy="6" r="2" fill="currentColor"></circle>
                      <circle cx="28" cy="10" r="2" fill="currentColor"></circle>
                      <circle cx="20" cy="12" r="2" fill="currentColor"></circle>
                      <circle cx="28" cy="22" r="2" fill="currentColor"></circle>
                      <circle cx="26" cy="28" r="2" fill="currentColor"></circle>
                      <circle cx="20" cy="26" r="2" fill="currentColor"></circle>
                      <circle cx="22" cy="20" r="2" fill="currentColor"></circle>
                      <circle cx="16" cy="4" r="2" fill="currentColor"></circle>
                      <circle cx="4" cy="24" r="2" fill="currentColor"></circle>
                      <circle cx="4" cy="16" r="2" fill="currentColor"></circle>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Text Classification</header>
                    <p className="text-sm text-gray-400">26,740 models</p>
                  </a>
                </div>
                <div className="first:hidden 2xl:first:block">
                  <a
                    className="transition:all dark:hover:brightness-120 relative flex h-52 w-[9.24rem] flex-none flex-col items-center justify-center rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white p-3 shadow-none duration-100 hover:translate-y-1 hover:shadow-inner hover:brightness-[102%] dark:from-gray-800 dark:to-gray-900 dark:!shadow-none"
                    style={{ boxShadow: '0 0px 16px 0 rgb(68 195 255 / 8%)' }}
                    href="/tasks/translation"
                  >
                    <svg
                      className="mx-auto mb-6 flex-none text-3xl text-green-400"
                      xmlns="http://www.w3.org/2000/svg"
                      xmlnsXlink="http://www.w3.org/1999/xlink"
                      aria-hidden="true"
                      fill="currentColor"
                      focusable="false"
                      role="img"
                      width="1em"
                      height="1em"
                      preserveAspectRatio="xMidYMid meet"
                      viewBox="0 0 18 18"
                    >
                      <path d="M15.7435 16.3688H16.9125L13.65 8.21251H12.3722L9.1097 16.3688H10.2788L11.1488 14.1938H14.8735L15.7435 16.3688ZM11.5838 13.1063L13.0084 9.53926L14.4385 13.1063H11.5838Z"></path>
                      <path d="M10.3875 4.40625V3.31875H6.58125V1.6875H5.49375V3.31875H1.6875V4.40625H7.52737C7.2261 5.64892 6.63129 6.80125 5.79281 7.76663C5.24624 7.08884 4.8246 6.31923 4.54763 5.49375H3.40575C3.74803 6.60116 4.30202 7.63159 5.037 8.52787C4.2247 9.3158 3.27338 9.94633 2.23125 10.3875L2.63906 11.3989C3.81007 10.9044 4.87658 10.1922 5.78194 9.3C6.67088 10.2044 7.73719 10.9153 8.91394 11.388L9.3 10.3875C8.25187 9.98235 7.3026 9.35754 6.516 8.55506C7.55705 7.36858 8.2892 5.94351 8.6475 4.40625H10.3875Z"></path>
                    </svg>
                    <header className="mb-2 text-center text-lg font-semibold leading-5">Translation</header>
                    <p className="text-sm text-gray-400">2,579 models</p>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="border-b border-gray-100 bg-gradient-to-bl from-purple-50 via-white to-blue-100/40 py-16 dark:from-gray-950 dark:to-gray-900 md:py-32">
          <div className="container grid gap-6 lg:grid-cols-3">
            <div className="lg:place-self-center lg:pr-12">
              <div className="flex flex-col">
                <svg
                  className="text-lg text-blue-400"
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
                    d="M12 14.195c-.176 0-.348-.046-.5-.133l-9-5.198a1 1 0 0 1 0-1.732l9-5.194c.31-.177.69-.177 1 0l9 5.194a1 1 0 0 1 0 1.732l-9 5.198a1.002 1.002 0 0 1-.5.133z"
                    opacity=".25"
                    fill="currentColor"
                  ></path>
                  <path
                    className="uim-tertiary"
                    d="M21.5 11.132l-1.964-1.134l-7.036 4.064c-.31.178-.69.178-1 0L4.464 9.998L2.5 11.132a1 1 0 0 0 0 1.732l9 5.198c.31.178.69.178 1 0l9-5.198a1 1 0 0 0 0-1.732z"
                    opacity=".5"
                    fill="currentColor"
                  ></path>
                  <path
                    className="uim-primary"
                    d="M21.5 15.132l-1.964-1.134l-7.036 4.064c-.31.178-.69.178-1 0l-7.036-4.064L2.5 15.132a1 1 0 0 0 0 1.732l9 5.198c.31.178.69.178 1 0l9-5.198a1 1 0 0 0 0-1.732z"
                    fill="currentColor"
                  ></path>
                </svg>
                <div className="h-2"></div>
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">Open Source</p>
                    <h2 className="false text-2xl font-semibold leading-tight text-gray-800">Transformers</h2>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  Transformers is our natural language processing library and our hub is now open to all ML models, with
                  support from libraries like
                  <a target="_blank" className="underline" href="https://github.com/flairNLP/flair" rel="noreferrer">
                    Flair
                  </a>
                  ,
                  <a
                    target="_blank"
                    className="underline"
                    href="https://github.com/asteroid-team/asteroid"
                    rel="noreferrer"
                  >
                    Asteroid
                  </a>
                  ,
                  <a target="_blank" className="underline" href="https://github.com/espnet/espnet" rel="noreferrer">
                    ESPnet
                  </a>
                  ,
                  <a
                    target="_blank"
                    className="underline"
                    href="https://github.com/pyannote/pyannote-audio"
                    rel="noreferrer"
                  >
                    Pyannote
                  </a>
                  , and more to come.
                </p>
                <div className="h-6"></div>
                <a
                  href="https://huggingface.co/transformers"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Read documentation
                </a>
              </div>
            </div>
            <div className="order-first gap-4 overflow-hidden rounded-lg object-cover md:order-none lg:col-span-2">
              <div className="dark:from-gray-925 flex items-center justify-center from-blue-100/20 to-blue-100/30 p-0 dark:to-gray-950 md:rounded-xl md:bg-gradient-to-b md:p-12">
                <div className="relative w-full overflow-hidden rounded-xl border border-gray-100 bg-gradient-to-br from-white to-white shadow-sm dark:from-gray-900 dark:to-gray-800 ">
                  <div className="absolute left-4 top-4 flex space-x-1.5">
                    <div className="h-2.5 w-2.5 cursor-pointer rounded-full bg-red-500 shadow-xl hover:bg-red-600"></div>
                    <div className="h-2.5 w-2.5 cursor-pointer rounded-full bg-orange-300 shadow-xl hover:bg-orange-400 dark:bg-orange-500 dark:hover:bg-orange-600"></div>
                    <div className="h-2.5 w-2.5 cursor-pointer rounded-full bg-green-500 shadow-xl hover:bg-green-600"></div>
                  </div>
                  <div className="pointer-events-none w-full truncate px-20 pt-3 text-center text-xs text-gray-300 dark:text-gray-600">
                    huggingface@transformers:~
                  </div>
                  <div className="px-4 pb-5 pt-3.5" translate="no">
                    <pre className="overflow-x-auto text-xs md:text-sm ">
                      <code className="leading-relaxed text-gray-600 md:leading-normal">
                        {/* <!-- HTML_TAG_START --> */}
                        <span className="hljs-keyword">from</span>
                        <span className="hljs-name">transformers</span>
                        <span className="hljs-keyword">import</span>
                        <span className="hljs-name">AutoTokenizer</span>,
                        <span className="hljs-name">AutoModelForMaskedLM</span>
                        <span className="hljs-name">tokenizer</span>= <span className="hljs-name">AutoTokenizer</span>.
                        <span className="hljs-title">from_pretrained</span>(
                        <span className="hljs-string">{`"bert-base-uncased"`}</span>)
                        <span className="hljs-name">model</span>=<span className="hljs-name">AutoModelForMaskedLM</span>.
                        <span className="hljs-title">from_pretrained</span>(
                        <span className="hljs-string">{`"bert-base-uncased"`}</span>){/* <!-- HTML_TAG_END --> */}
                      </code>
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-white via-gray-200/20 to-white py-16 dark:from-gray-950 dark:to-gray-900 md:py-32">
          <div className="container grid gap-x-6 gap-y-12 lg:grid-cols-3 lg:gap-y-0">
            <div className="lg:place-self-center lg:pr-12">
              <div className="flex flex-col">
                <svg
                  className="text-2xl text-indigo-400"
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
                  <path d="M8 9H4a2 2 0 0 0-2 2v12h2v-5h4v5h2V11a2 2 0 0 0-2-2zm-4 7v-5h4v5z" fill="currentColor"></path>
                  <path d="M22 11h3v10h-3v2h8v-2h-3V11h3V9h-8v2z" fill="currentColor"></path>
                  <path d="M14 23h-2V9h6a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-4zm0-7h4v-5h-4z" fill="currentColor"></path>
                </svg>
                <div className="h-2"></div>
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">On demand</p>
                    <h2 className="false text-2xl font-semibold leading-tight text-gray-800">Inference API</h2>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  Serve your models directly from Hugging Face infrastructure and run large scale NLP models in
                  milliseconds with just a few lines of code.
                </p>
                <div className="h-6"></div>
                <a
                  href="/inference-api"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Learn more
                </a>
              </div>
            </div>
            <div className="dark:border-gray-850 dark:from-gray-925 flex flex-col overflow-hidden rounded-xl bg-gradient-to-br from-white to-white p-6 shadow-sm dark:to-gray-950">
              <div className="truncate">
                <a href="/distilbert-base-uncased" className="text-lg font-semibold">
                  distilbert-base-uncased
                </a>
              </div>
              <div className="flex w-full flex-1">
                <div
                  className="SVELTE_HYDRATER contents"
                  data-props='{"apiUrl":"https://api-inference.huggingface.co","callApiOnMount":true,"model":{"pipeline_tag":"fill-mask","mask_token":"[MASK]","id":"distilbert-base-uncased","private":false,"widgetData":[{"text":"The goal of life is [MASK]."}]},"noTitle":true,"includeCredentials":true}'
                  data-target="InferenceWidget"
                >
                  <div className="flex w-full max-w-full flex-col ">
                    <div className="mb-2 flex items-center font-semibold"></div>
                    <div className="mb-0.5 flex w-full max-w-full flex-wrap items-center justify-between text-sm text-gray-500">
                      <a
                        className="hover:underline"
                        href="/tasks/fill-mask"
                        target="_blank"
                        title="Learn more about fill-mask"
                      >
                        <div className="mb-1.5 mr-2 inline-flex items-center">
                          <svg
                            className="mr-1"
                            xmlns="http://www.w3.org/2000/svg"
                            xmlnsXlink="http://www.w3.org/1999/xlink"
                            aria-hidden="true"
                            fill="currentColor"
                            focusable="false"
                            role="img"
                            width="1em"
                            height="1em"
                            preserveAspectRatio="xMidYMid meet"
                            viewBox="0 0 18 19"
                          >
                            <path d="M12.3625 13.85H10.1875V12.7625H12.3625V10.5875H13.45V12.7625C13.4497 13.0508 13.335 13.3272 13.1312 13.5311C12.9273 13.735 12.6508 13.8497 12.3625 13.85V13.85Z"></path>
                            <path d="M5.8375 8.41246H4.75V6.23746C4.75029 5.94913 4.86496 5.67269 5.06884 5.4688C5.27272 5.26492 5.54917 5.15025 5.8375 5.14996H8.0125V6.23746H5.8375V8.41246Z"></path>
                            <path d="M15.625 5.14998H13.45V2.97498C13.4497 2.68665 13.335 2.4102 13.1312 2.20632C12.9273 2.00244 12.6508 1.88777 12.3625 1.88748H2.575C2.28666 1.88777 2.01022 2.00244 1.80633 2.20632C1.60245 2.4102 1.48778 2.68665 1.4875 2.97498V12.7625C1.48778 13.0508 1.60245 13.3273 1.80633 13.5311C2.01022 13.735 2.28666 13.8497 2.575 13.85H4.75V16.025C4.75028 16.3133 4.86495 16.5898 5.06883 16.7936C5.27272 16.9975 5.54916 17.1122 5.8375 17.1125H15.625C15.9133 17.1122 16.1898 16.9975 16.3937 16.7936C16.5975 16.5898 16.7122 16.3133 16.7125 16.025V6.23748C16.7122 5.94915 16.5975 5.6727 16.3937 5.46882C16.1898 5.26494 15.9133 5.15027 15.625 5.14998V5.14998ZM15.625 16.025H5.8375V13.85H8.0125V12.7625H5.8375V10.5875H4.75V12.7625H2.575V2.97498H12.3625V5.14998H10.1875V6.23748H12.3625V8.41248H13.45V6.23748H15.625V16.025Z"></path>
                          </svg>
                          <span>Fill-Mask</span>
                        </div>
                      </a>
                      <div className="ml-auto flex gap-x-1">
                        <div className="false false  relative mb-1.5">
                          <div className="inline-flex w-32 justify-between rounded-md border border-gray-100 px-4 py-1">
                            <div className="truncate text-sm">Examples</div>
                            <svg
                              className="false -mr-1 ml-2 h-5 w-5 transform transition ease-in-out"
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                              aria-hidden="true"
                            >
                              <path
                                fillRule="evenodd"
                                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              ></path>
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                    <form>
                      <div className="mb-1.5 text-sm text-gray-500">
                        Mask token: <code>[MASK]</code>
                      </div>
                      <label className="block ">
                        <span
                          className="  dark:bg-gray-925 svelte-1wfa7x9 inline-block max-h-[500px] min-h-[42px] w-full resize-y overflow-auto whitespace-pre-wrap rounded-lg border border-gray-200 px-3 py-2 shadow-inner outline-none focus:shadow-inner focus:ring focus:ring-blue-200"
                          role="textbox"
                          contentEditable={undefined}
                          // style={ "--placeholder": 'Your sentence here...' }
                          spellCheck="false"
                          dir="auto"
                        >
                          The goal of life is [MASK].
                        </span>
                      </label>
                      <button className="btn-widget mt-2 h-10 w-24 px-5" type="submit">
                        Compute
                      </button>
                    </form>
                    <div className="mt-2">
                      <div className="text-xs text-gray-400">
                        Computation time on Intel Xeon 3rd Gen Scalable cpu: cached
                      </div>
                    </div>
                    <div className="space-y-3.5 pt-4">
                      <div
                        className="animate__animated animate__fadeIn false flex items-start justify-between font-mono text-xs leading-none transition duration-200 ease-in-out"
                        style={{ animationDelay: '0s' }}
                      >
                        <div className="flex-1">
                          <div
                            className="mb-1 h-1 rounded bg-gradient-to-r from-purple-400 to-purple-200 dark:from-purple-400 dark:to-purple-600"
                            style={{ width: '80%' }}
                          ></div>
                          <span className="leading-snug">happiness</span>
                        </div>
                        <span className="pl-2">0.036</span>
                      </div>
                      <div
                        className="animate__animated animate__fadeIn false flex items-start justify-between font-mono text-xs leading-none transition duration-200 ease-in-out"
                        style={{ animationDelay: '0.04s' }}
                      >
                        <div className="flex-1">
                          <div
                            className="mb-1 h-1 rounded bg-gradient-to-r from-purple-400 to-purple-200 dark:from-purple-400 dark:to-purple-600"
                            style={{ width: '68%' }}
                          ></div>
                          <span className="leading-snug">survival</span>
                        </div>
                        <span className="pl-2">0.031</span>
                      </div>
                      <div
                        className="animate__animated animate__fadeIn false flex items-start justify-between font-mono text-xs leading-none transition duration-200 ease-in-out"
                        style={{ animationDelay: '0.08s' }}
                      >
                        <div className="flex-1">
                          <div
                            className="mb-1 h-1 rounded bg-gradient-to-r from-purple-400 to-purple-200 dark:from-purple-400 dark:to-purple-600"
                            style={{ width: '38%' }}
                          ></div>
                          <span className="leading-snug">salvation</span>
                        </div>
                        <span className="pl-2">0.017</span>
                      </div>
                      <div
                        className="animate__animated animate__fadeIn false flex items-start justify-between font-mono text-xs leading-none transition duration-200 ease-in-out"
                        style={{ animationDelay: '0.12s' }}
                      >
                        <div className="flex-1">
                          <div
                            className="mb-1 h-1 rounded bg-gradient-to-r from-purple-400 to-purple-200 dark:from-purple-400 dark:to-purple-600"
                            style={{ width: '37%' }}
                          ></div>
                          <span className="leading-snug">freedom</span>
                        </div>
                        <span className="pl-2">0.017</span>
                      </div>
                      <div
                        className="animate__animated animate__fadeIn false flex items-start justify-between font-mono text-xs leading-none transition duration-200 ease-in-out"
                        style={{ animationDelay: '0.16s' }}
                      >
                        <div className="flex-1">
                          <div
                            className="mb-1 h-1 rounded bg-gradient-to-r from-purple-400 to-purple-200 dark:from-purple-400 dark:to-purple-600"
                            style={{ width: '34%' }}
                          ></div>
                          <span className="leading-snug">unity</span>
                        </div>
                        <span className="pl-2">0.015</span>
                      </div>
                    </div>
                    <div className="mt-auto flex items-center pt-4 text-xs text-gray-500">
                      <button className="flex items-center ">
                        <svg
                          className="mr-1"
                          xmlns="http://www.w3.org/2000/svg"
                          xmlnsXlink="http://www.w3.org/1999/xlink"
                          aria-hidden="true"
                          focusable="false"
                          role="img"
                          width="1em"
                          height="1em"
                          preserveAspectRatio="xMidYMid meet"
                          viewBox="0 0 32 32"
                          style={{ transform: 'rotate(360deg)' }}
                        >
                          <path d="M31 16l-7 7l-1.41-1.41L28.17 16l-5.58-5.59L24 9l7 7z" fill="currentColor"></path>
                          <path d="M1 16l7-7l1.41 1.41L3.83 16l5.58 5.59L8 23l-7-7z" fill="currentColor"></path>
                          <path d="M12.419 25.484L17.639 6l1.932.518L14.35 26z" fill="currentColor"></path>
                        </svg>
                        JSON Output
                      </button>
                      <button className="ml-auto flex items-center">
                        <svg
                          className="mr-1"
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
                          <path d="M22 16h2V8h-8v2h6v6z" fill="currentColor"></path>
                          <path d="M8 24h8v-2h-6v-6H8v8z" fill="currentColor"></path>
                          <path
                            d="M26 28H6a2.002 2.002 0 0 1-2-2V6a2.002 2.002 0 0 1 2-2h20a2.002 2.002 0 0 1 2 2v20a2.002 2.002 0 0 1-2 2zM6 6v20h20.001L26 6z"
                            fill="currentColor"
                          ></path>
                        </svg>
                        Maximize
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="dark:border-gray-850 dark:from-gray-925 flex flex-col overflow-hidden rounded-xl bg-gradient-to-br from-white to-white p-6 shadow-sm dark:to-gray-950">
              <div className="truncate">
                <a href="/dbmdz/bert-large-cased-finetuned-conll03-english" className="text-lg font-semibold">
                  dbmdz/bert-large-cased-finetuned-conll03-english
                </a>
              </div>
              <div className="flex w-full flex-1">
                <div
                  className="SVELTE_HYDRATER contents"
                  data-props='{"apiUrl":"https://api-inference.huggingface.co","callApiOnMount":true,"model":{"pipeline_tag":"token-classification","id":"dbmdz/bert-large-cased-finetuned-conll03-english","private":false,"widgetData":[{"text":"My name is Clara and I live in Berkeley, California. I work at this cool company called Hugging Face."}]},"noTitle":true,"includeCredentials":true}'
                  data-target="InferenceWidget"
                >
                  <div className="flex w-full max-w-full flex-col ">
                    <div className="mb-2 flex items-center font-semibold"></div>
                    <div className="mb-0.5 flex w-full max-w-full flex-wrap items-center justify-between text-sm text-gray-500">
                      <a
                        className="hover:underline"
                        href="/tasks/token-classification"
                        target="_blank"
                        title="Learn more about token-classification"
                      >
                        <div className="mb-1.5 mr-2 inline-flex items-center">
                          <svg
                            className="mr-1"
                            xmlns="http://www.w3.org/2000/svg"
                            xmlnsXlink="http://www.w3.org/1999/xlink"
                            aria-hidden="true"
                            fill="currentColor"
                            focusable="false"
                            role="img"
                            width="1em"
                            height="1em"
                            preserveAspectRatio="xMidYMid meet"
                            viewBox="0 0 18 18"
                          >
                            <path d="M11.075 10.1875H12.1625V11.275H11.075V10.1875Z"></path>
                            <path d="M15.425 9.10004H16.5125V10.1875H15.425V9.10004Z"></path>
                            <path d="M7.8125 3.66254H8.9V4.75004H7.8125V3.66254Z"></path>
                            <path d="M8.90001 12.3625H6.72501V9.09998C6.72472 8.81165 6.61005 8.5352 6.40617 8.33132C6.20228 8.12744 5.92584 8.01277 5.63751 8.01248H2.37501C2.08667 8.01277 1.81023 8.12744 1.60635 8.33132C1.40246 8.5352 1.28779 8.81165 1.28751 9.09998V12.3625C1.28779 12.6508 1.40246 12.9273 1.60635 13.1311C1.81023 13.335 2.08667 13.4497 2.37501 13.45H5.63751V15.625C5.63779 15.9133 5.75246 16.1898 5.95635 16.3936C6.16023 16.5975 6.43667 16.7122 6.72501 16.7125H8.90001C9.18834 16.7122 9.46478 16.5975 9.66867 16.3936C9.87255 16.1898 9.98722 15.9133 9.98751 15.625V13.45C9.98722 13.1616 9.87255 12.8852 9.66867 12.6813C9.46478 12.4774 9.18834 12.3628 8.90001 12.3625V12.3625ZM2.37501 12.3625V9.09998H5.63751V12.3625H2.37501ZM6.72501 15.625V13.45H8.90001V15.625H6.72501Z"></path>
                            <path d="M15.425 16.7125H13.25C12.9617 16.7122 12.6852 16.5976 12.4813 16.3937C12.2775 16.1898 12.1628 15.9134 12.1625 15.625V13.45C12.1628 13.1617 12.2775 12.8852 12.4813 12.6814C12.6852 12.4775 12.9617 12.3628 13.25 12.3625H15.425C15.7133 12.3628 15.9898 12.4775 16.1937 12.6814C16.3976 12.8852 16.5122 13.1617 16.5125 13.45V15.625C16.5122 15.9134 16.3976 16.1898 16.1937 16.3937C15.9898 16.5976 15.7133 16.7122 15.425 16.7125ZM13.25 13.45V15.625H15.425V13.45H13.25Z"></path>
                            <path d="M15.425 1.48752H12.1625C11.8742 1.48781 11.5977 1.60247 11.3938 1.80636C11.19 2.01024 11.0753 2.28668 11.075 2.57502V5.83752H9.98751C9.69917 5.83781 9.42273 5.95247 9.21885 6.15636C9.01496 6.36024 8.9003 6.63668 8.90001 6.92502V8.01252C8.9003 8.30085 9.01496 8.5773 9.21885 8.78118C9.42273 8.98506 9.69917 9.09973 9.98751 9.10002H11.075C11.3633 9.09973 11.6398 8.98506 11.8437 8.78118C12.0476 8.5773 12.1622 8.30085 12.1625 8.01252V6.92502H15.425C15.7133 6.92473 15.9898 6.81006 16.1937 6.60618C16.3976 6.4023 16.5122 6.12585 16.5125 5.83752V2.57502C16.5122 2.28668 16.3976 2.01024 16.1937 1.80636C15.9898 1.60247 15.7133 1.48781 15.425 1.48752ZM9.98751 8.01252V6.92502H11.075V8.01252H9.98751ZM12.1625 5.83752V2.57502H15.425V5.83752H12.1625Z"></path>
                            <path d="M4.55001 5.83752H2.37501C2.08667 5.83723 1.81023 5.72256 1.60635 5.51868C1.40246 5.3148 1.28779 5.03835 1.28751 4.75002V2.57502C1.28779 2.28668 1.40246 2.01024 1.60635 1.80636C1.81023 1.60247 2.08667 1.48781 2.37501 1.48752H4.55001C4.83834 1.48781 5.11478 1.60247 5.31867 1.80636C5.52255 2.01024 5.63722 2.28668 5.63751 2.57502V4.75002C5.63722 5.03835 5.52255 5.3148 5.31867 5.51868C5.11478 5.72256 4.83834 5.83723 4.55001 5.83752V5.83752ZM2.37501 2.57502V4.75002H4.55001V2.57502H2.37501Z"></path>
                          </svg>
                          <span>Token Classification</span>
                        </div>
                      </a>
                      <div className="ml-auto flex gap-x-1">
                        <div className="false false  relative mb-1.5">
                          <div className="inline-flex w-32 justify-between rounded-md border border-gray-100 px-4 py-1">
                            <div className="truncate text-sm">Examples</div>
                            <svg
                              className="false -mr-1 ml-2 h-5 w-5 transform transition ease-in-out"
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                              aria-hidden="true"
                            >
                              <path
                                fillRule="evenodd"
                                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              ></path>
                            </svg>
                          </div>
                        </div>
                      </div>
                    </div>
                    <form>
                      <label className="block ">
                        <span
                          className="  dark:bg-gray-925 svelte-1wfa7x9 inline-block max-h-[500px] min-h-[42px] w-full resize-y overflow-auto whitespace-pre-wrap rounded-lg border border-gray-200 px-3 py-2 shadow-inner outline-none focus:shadow-inner focus:ring focus:ring-blue-200"
                          role="textbox"
                          contentEditable={undefined}
                          // style="--placeholder: 'Your sentence here...';"
                          spellCheck="false"
                          dir="auto"
                        >
                          My name is Clara and I live in Berkeley, California. I work at this cool company called Hugging
                          Face.
                        </span>
                      </label>
                      <button className="btn-widget mt-2 h-10 w-24 px-5" type="submit">
                        Compute
                      </button>
                    </form>
                    <div className="mt-2">
                      <div className="text-xs text-gray-400">
                        Computation time on Intel Xeon 3rd Gen Scalable cpu: cached
                      </div>
                    </div>
                    <div className="mt-2 leading-8 text-gray-800">
                      My name is
                      <span
                        data-entity="PER"
                        data-hash="7"
                        data-index=""
                        className="rounded bg-pink-100 px-1 py-0.5 text-pink-800 dark:bg-pink-700 dark:text-pink-100"
                      >
                        Clara
                        <span className="ml-1 select-none rounded bg-pink-500 px-0.5 text-xs font-semibold text-pink-100">
                          PER
                        </span>
                      </span>
                      and I live in
                      <span
                        data-entity="LOC"
                        data-hash="6"
                        data-index=""
                        className="rounded bg-fuchsia-100 px-1 py-0.5 text-fuchsia-800 dark:bg-fuchsia-700 dark:text-fuchsia-100"
                      >
                        Berkeley
                        <span className="ml-1 select-none rounded bg-fuchsia-500 px-0.5 text-xs font-semibold text-fuchsia-100">
                          LOC
                        </span>
                      </span>
                      ,
                      <span
                        data-entity="LOC"
                        data-hash="6"
                        data-index=""
                        className="rounded bg-fuchsia-100 px-1 py-0.5 text-fuchsia-800 dark:bg-fuchsia-700 dark:text-fuchsia-100"
                      >
                        California
                        <span className="ml-1 select-none rounded bg-fuchsia-500 px-0.5 text-xs font-semibold text-fuchsia-100">
                          LOC
                        </span>
                      </span>
                      . I work at this cool company called
                      <span
                        data-entity="ORG"
                        data-hash="0"
                        data-index=""
                        className="rounded bg-teal-100 px-1 py-0.5 text-teal-800 dark:bg-teal-700 dark:text-teal-100"
                      >
                        Hugging Face
                        <span className="ml-1 select-none rounded bg-teal-500 px-0.5 text-xs font-semibold text-teal-100">
                          ORG
                        </span>
                      </span>
                      .
                    </div>
                    <div className="mt-auto flex items-center pt-4 text-xs text-gray-500">
                      <button className="flex items-center ">
                        <svg
                          className="mr-1"
                          xmlns="http://www.w3.org/2000/svg"
                          xmlnsXlink="http://www.w3.org/1999/xlink"
                          aria-hidden="true"
                          focusable="false"
                          role="img"
                          width="1em"
                          height="1em"
                          preserveAspectRatio="xMidYMid meet"
                          viewBox="0 0 32 32"
                          style={{ transform: 'rotate(360deg)' }}
                        >
                          <path d="M31 16l-7 7l-1.41-1.41L28.17 16l-5.58-5.59L24 9l7 7z" fill="currentColor"></path>
                          <path d="M1 16l7-7l1.41 1.41L3.83 16l5.58 5.59L8 23l-7-7z" fill="currentColor"></path>
                          <path d="M12.419 25.484L17.639 6l1.932.518L14.35 26z" fill="currentColor"></path>
                        </svg>
                        JSON Output
                      </button>
                      <button className="ml-auto flex items-center">
                        <svg
                          className="mr-1"
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
                          <path d="M22 16h2V8h-8v2h6v6z" fill="currentColor"></path>
                          <path d="M8 24h8v-2h-6v-6H8v8z" fill="currentColor"></path>
                          <path
                            d="M26 28H6a2.002 2.002 0 0 1-2-2V6a2.002 2.002 0 0 1 2-2h20a2.002 2.002 0 0 1 2 2v20a2.002 2.002 0 0 1-2 2zM6 6v20h20.001L26 6z"
                            fill="currentColor"
                          ></path>
                        </svg>
                        Maximize
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="py-16 md:py-32">
          <div className="container grid gap-10 lg:grid-cols-4">
            <div className="md:from-gray-50-to-white flex flex-col rounded-tl-lg md:bg-gradient-to-br md:pl-6 md:pt-6 lg:col-span-2">
              <svg
                className="mb-2 text-3xl text-teal-400"
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
                  d="M19.108 12.376q-.176-.201-.371-.403q.136-.144.264-.287c1.605-1.804 2.283-3.614 1.655-4.701c-.602-1.043-2.393-1.354-4.636-.918q-.331.065-.659.146q-.063-.216-.133-.43C14.467 3.49 13.238 1.999 11.982 2c-1.204 0-2.368 1.397-3.111 3.558q-.11.32-.203.644q-.219-.054-.44-.1c-2.366-.485-4.271-.165-4.898.924c-.601 1.043.027 2.75 1.528 4.472q.224.255.46.5c-.186.19-.361.381-.525.571c-1.465 1.698-2.057 3.376-1.457 4.415c.62 1.074 2.498 1.425 4.785.975q.278-.055.553-.124q.1.351.221.697C9.635 20.649 10.792 22 11.992 22c1.24 0 2.482-1.453 3.235-3.659c.06-.174.115-.355.169-.541q.355.088.715.156c2.203.417 3.952.09 4.551-.95c.619-1.075-.02-2.877-1.554-4.63zM4.07 7.452c.386-.67 1.943-.932 3.986-.512q.196.04.399.09a20.464 20.464 0 0 0-.422 2.678A20.887 20.887 0 0 0 5.93 11.4q-.219-.227-.427-.465C4.216 9.461 3.708 8.081 4.07 7.452zm3.887 5.728c-.51-.387-.985-.783-1.416-1.181c.43-.396.905-.79 1.415-1.176q-.028.589-.027 1.179q0 .59.028 1.178zm0 3.94a7.237 7.237 0 0 1-2.64.094a1.766 1.766 0 0 1-1.241-.657c-.365-.63.111-1.978 1.364-3.43q.236-.273.488-.532a20.49 20.49 0 0 0 2.107 1.7a20.802 20.802 0 0 0 .426 2.712q-.25.063-.505.114zm7.1-8.039q-.503-.317-1.018-.613q-.508-.292-1.027-.563c.593-.249 1.176-.462 1.739-.635a18.218 18.218 0 0 1 .306 1.811zM9.68 5.835c.636-1.85 1.578-2.98 2.304-2.98c.773-.001 1.777 1.218 2.434 3.197q.064.194.12.39a20.478 20.478 0 0 0-2.526.97a20.061 20.061 0 0 0-2.52-.981q.087-.3.188-.596zm-.4 1.424a18.307 18.307 0 0 1 1.73.642q-1.052.542-2.048 1.181c.08-.638.187-1.249.318-1.823zm-.317 7.66q.497.319 1.009.613q.522.3 1.057.576a18.196 18.196 0 0 1-1.744.665a19.144 19.144 0 0 1-.322-1.853zm5.456 3.146a7.236 7.236 0 0 1-1.238 2.333a1.766 1.766 0 0 1-1.188.748c-.729 0-1.658-1.085-2.29-2.896q-.112-.321-.206-.648a20.109 20.109 0 0 0 2.53-1.01a20.8 20.8 0 0 0 2.547.979q-.072.249-.155.494zm.362-1.324c-.569-.176-1.16-.393-1.762-.646q.509-.267 1.025-.565q.53-.306 1.032-.627a18.152 18.152 0 0 1-.295 1.838zm.447-4.743q0 .911-.057 1.82c-.493.334-1.013.66-1.554.972c-.54.311-1.073.597-1.597.856q-.827-.396-1.622-.854q-.79-.455-1.544-.969q-.07-.91-.07-1.822q0-.911.068-1.821a24.168 24.168 0 0 1 3.158-1.823q.816.397 1.603.851q.79.454 1.55.959q.065.914.065 1.831zm.956-5.093c1.922-.373 3.37-.122 3.733.507c.387.67-.167 2.148-1.554 3.706q-.115.129-.238.259a20.061 20.061 0 0 0-2.144-1.688a20.04 20.04 0 0 0-.405-2.649q.31-.076.608-.135zm-.13 3.885a18.164 18.164 0 0 1 1.462 1.188a18.12 18.12 0 0 1-1.457 1.208q.023-.594.023-1.188q0-.604-.028-1.208zm3.869 5.789c-.364.631-1.768.894-3.653.538q-.324-.061-.664-.146a20.069 20.069 0 0 0 .387-2.682a19.94 19.94 0 0 0 2.137-1.715q.177.183.336.364a7.234 7.234 0 0 1 1.403 2.238a1.766 1.766 0 0 1 .054 1.403zm-8.819-6.141a1.786 1.786 0 1 0 2.44.654a1.786 1.786 0 0 0-2.44-.654z"
                  fill="currentColor"
                ></path>
              </svg>
              <div className="font-mono text-sm text-gray-400">Science</div>
              <h2 className="mb-4 text-2xl font-semibold">Our Research contributions</h2>
              <p className="max-w-md text-gray-500">
                We’re on a journey to advance and democratize NLP for everyone. Along the way, we contribute to the
                development of technology for the better.
              </p>
            </div>
            <div className="bg-white">
              <div className="mb-6 flex h-36 items-center justify-center rounded-lg bg-gradient-to-r from-pink-50 to-white shadow-inner dark:from-gray-900 dark:to-gray-950">
                <p className="text-6xl">🌸</p>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">T0</p>
                    <h3 className="false font-semibold leading-tight text-gray-800">
                      Multitask Prompted Training Enables Zero-Shot Task Generalization
                    </h3>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  Open source state-of-the-art zero-shot language model out of
                  <a href="https://bigscience.huggingface.co/" target="_blank" rel="noreferrer">
                    BigScience
                  </a>
                  .
                </p>
                <div className="h-6"></div>
                <a
                  href="https://bigscience.huggingface.co/blog/t0"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Read more
                </a>
              </div>
            </div>
            <div className="bg-white">
              <div className="mb-6 flex h-36 items-center justify-center rounded-lg bg-gradient-to-r from-green-50 to-white shadow-inner dark:from-gray-900 dark:to-gray-950">
                <p className="text-6xl">🐎</p>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">DistilBERT</p>
                    <h3 className="false font-semibold leading-tight text-gray-800">
                      DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter
                    </h3>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  A smaller, faster, lighter, cheaper version of BERT obtained via model distillation.
                </p>
                <div className="h-6"></div>
                <a
                  href="https://medium.com/huggingface/distilbert-8cf3380435b5"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Read more
                </a>
              </div>
            </div>
            <div className="bg-white">
              <div className="mb-6 flex h-36 items-center justify-center rounded-lg bg-gradient-to-r from-teal-50 to-white shadow-inner dark:from-gray-900 dark:to-gray-950">
                <p className="text-6xl">📚</p>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">HMTL</p>
                    <h3 className="false font-semibold leading-tight text-gray-800">Hierarchical Multi-Task Learning</h3>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  Learning embeddings from semantic tasks for multi-task learning. We have open-sourced code and a demo.
                </p>
                <div className="h-6"></div>
                <a
                  href="https://arxiv.org/abs/1811.06031"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Read more
                </a>
              </div>
            </div>
            <div className="bg-white">
              <div className="mb-6 flex h-36 items-center justify-center rounded-lg bg-gradient-to-r from-indigo-50 to-white shadow-inner dark:from-gray-900 dark:to-gray-950">
                <p className="text-6xl">🐸</p>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">Dynamical Language Models</p>
                    <h3 className="false font-semibold leading-tight text-gray-800">
                      Meta-learning for language modeling
                    </h3>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  A meta learner is trained via gradient descent to continuously and dynamically update language model
                  weights.
                </p>
                <div className="h-6"></div>
                <a
                  href="https://arxiv.org/abs/1803.10631"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Read more
                </a>
              </div>
            </div>
            <div className="bg-white">
              <div className="mb-6 flex h-36 items-center justify-center rounded-lg bg-gradient-to-r from-pink-50 to-white shadow-inner dark:from-gray-900 dark:to-gray-950">
                <p className="text-6xl">🤖</p>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">State of the art</p>
                    <h3 className="false font-semibold leading-tight text-gray-800">Neuralcoref</h3>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  Our open source coreference resolution library for coreference. You can train it on your own dataset and
                  language.
                </p>
                <div className="h-6"></div>
                <a
                  href="/coref"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Read more
                </a>
              </div>
            </div>
            <div className="bg-white">
              <div className="mb-6 flex h-36 items-center justify-center rounded-lg bg-gradient-to-r from-purple-50 via-purple-50 to-white shadow-inner dark:from-gray-900 dark:to-gray-950">
                <p className="text-7xl">🦄</p>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center rounded-lg">
                  <div>
                    <p className="font-mono text-sm text-gray-500">Auto-complete your thoughts</p>
                    <h3 className="false font-semibold leading-tight text-gray-800">Write with Transformers</h3>
                  </div>
                </div>
                <div className="h-6"></div>
                <p className="leading-snug text-gray-500">
                  This web app is the official demo of the Transformers repository &#39;s text generation capabilities.
                </p>
                <div className="h-6"></div>
                <a
                  href="https://transformer.huggingface.co/"
                  className="mt-auto self-start border-b border-gray-600 pb-0.5 text-gray-800 hover:border-gray-400 hover:text-gray-500"
                >
                  Start writing
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>
    )
  }