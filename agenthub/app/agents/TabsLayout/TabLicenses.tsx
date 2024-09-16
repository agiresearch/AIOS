import { LicenseSVG } from '@/ui/svgs'

import { DatasetsLicense } from '../const'

export default function TabLicenses() {
  return (
    <div className="mb-3">
      <div className="flex flex-wrap">
        {DatasetsLicense.map((item, index) => (
          <a key={index} className="tag  tag-white rounded-full" href={`/datasets?license=license%3A${item}`}>
            <LicenseSVG />
            <span>{item}</span>
          </a>
        ))}
      </div>
    </div>
  )
}
