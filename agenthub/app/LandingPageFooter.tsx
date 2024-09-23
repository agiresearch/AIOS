export default function LandingPageFooter() {
    return (
      <footer className="border-t border-gray-100">
        <div className="container pb-32 pt-12">
          <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
            <div>
              <div className="mb-4 text-lg font-semibold">Website</div>
              <ul className="space-y-1 text-gray-600 md:space-y-2">
                <li>
                  <a className="hover:underline" href="/models">
                    Models
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/datasets">
                    Datasets
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/spaces">
                    Spaces
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/tasks">
                    Tasks
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/inference-endpoints">
                    Expert Support
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/support">
                    Expert Acceleration Program
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <div className="mb-4 text-lg font-semibold">Company</div>
              <ul className="space-y-1 text-gray-600 md:space-y-2">
                <li>
                  <a className="hover:underline" href="/huggingface">
                    About
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/shop">
                    HF Store
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/brand">
                    Brand assets
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/terms-of-service">
                    Terms of service
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/privacy">
                    Privacy
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="https://apply.workable.com/huggingface/">
                    Jobs
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="mailto:press@huggingface.co">
                    Press
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <div className="mb-4 text-lg font-semibold">Resources</div>
              <ul className="space-y-1 text-gray-600 md:space-y-2">
                <li>
                  <a className="hover:underline" href="/learn">
                    Learn
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/docs">
                    Documentation
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/blog">
                    Blog
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="https://discuss.huggingface.co">
                    Forum
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="https://status.huggingface.co/">
                    Service Status
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <div className="mb-4 text-lg font-semibold">Social</div>
              <ul className="space-y-1 text-gray-600 md:space-y-2">
                <li>
                  <a className="hover:underline" href="https://github.com/huggingface">
                    GitHub
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="https://twitter.com/huggingface">
                    Twitter
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="https://www.linkedin.com/company/huggingface/">
                    LinkedIn
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="/join/discord">
                    Discord
                  </a>
                </li>
                <li>
                  <a className="hover:underline" href="https://www.zhihu.com/org/huggingface">
                    Zhihu
                  </a>
                </li>
                <li>
                  <a
                    target="_blank"
                    className="hover:underline"
                    href="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/chinese-language-blog/wechat.jpg"
                    rel="noreferrer"
                  >
                    WeChat
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    )
  }