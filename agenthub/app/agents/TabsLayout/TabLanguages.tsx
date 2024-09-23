import { LanguageSVG } from '@/ui/svgs'

import { DatasetLanguages } from '../const'

export default function TabLanguages() {
  return (
    <div className="mb-3">
      <div className="flex flex-wrap">
        {DatasetLanguages.map((lang, index) => (
          <a key={index} className="tag  tag-green" href={`/datasets?language=language%3A${lang}`}>
            <LanguageSVG />
            <span>{lang}</span>
          </a>
        ))}
      </div>
    </div>
  )
}
