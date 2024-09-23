export default function TabSizes() {
  return (
    <div className="mb-3">
      <div className="flex flex-wrap">
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3An%3C1K">
          <span>n&lt;1K</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A1K%3Cn%3C10K">
          <span>1K&lt;n&lt;10K</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A10K%3Cn%3C100K">
          <span>10K&lt;n&lt;100K</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A100K%3Cn%3C1M">
          <span>100K&lt;n&lt;1M</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A1M%3Cn%3C10M">
          <span>1M&lt;n&lt;10M</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A10M%3Cn%3C100M">
          <span>10M&lt;n&lt;100M</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A100M%3Cn%3C1B">
          <span>100M&lt;n&lt;1B</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A1B%3Cn%3C10B">
          <span>1B&lt;n&lt;10B</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A10B%3Cn%3C100B">
          <span>10B&lt;n&lt;100B</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3A100B%3Cn%3C1T">
          <span>100B&lt;n&lt;1T</span>
        </a>
        <a className="tag  tag-orange" href="/datasets?size_categories=size_categories%3An%3E1T">
          <span>n&gt;1T</span>
        </a>
      </div>
    </div>
  )
}
