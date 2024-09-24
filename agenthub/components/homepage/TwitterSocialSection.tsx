import Link from 'next/link'
import { MessageCircle } from 'lucide-react'
import { Button } from '@nextui-org/react'
import SectionContainer from './SectionContainer'
import TwitterSocialProof from './TwitterSocialProof'
// import TwitterSocialProofMobile from './Sections/TwitterSocialProofMobile'

import { Tweets } from './Tweets'

const TwitterSocialSection = () => {
  const tweets = Tweets.slice(0, 18)

  return (
    <>
      <SectionContainer className="w-full text-center !pb-0">
        <h3 className="h2">Join the community</h3>
        <p className="p">Discover what our community has to say about their Supabase experience.</p>
        <div className="my-8 flex justify-center gap-2">
          <Button 
          size='sm' > 
           {/* asChild size="sm" iconRight={<MessageCircle size={14} />} type="default"> */}
            <Link
              href={'https://github.com/supabase/supabase/discussions'}
              target="_blank"
              tabIndex={-1}
            >
              GitHub discussions
            </Link>
          </Button>
          <Button 
          size='sm'>
          {/* asChild type="default" size="small" iconRight={<MessageCircle size={14} />}> */}
            <Link href={'https://discord.supabase.com/'} target="_blank" tabIndex={-1}>
              Discord
            </Link>
          </Button>
        </div>
      </SectionContainer>
      <SectionContainer className="relative w-full !px-0 lg:!px-16 xl:!px-0 !pb-0 mb-16 md:mb-12 lg:mb-12 !pt-6 max-w-[1400px]">
        {/* <TwitterSocialProofMobile className="lg:hidden -mb-24" tweets={tweets} /> */}
        <TwitterSocialProof className="hidden lg:flex" />
      </SectionContainer>
    </>
  )
}

export default TwitterSocialSection