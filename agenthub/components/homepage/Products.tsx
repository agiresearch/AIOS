// import Button from 'ui'
import { Link } from '@nextui-org/react'

import SectionContainer from './SectionContainer'
import ExampleCard from './ExampleCard'

const isDevEnv = process.env.NODE_ENV == "development"

const Examples = [
    {
      type: 'example',
      tags: ['Next.js', 'Stripe', 'Vercel'],
      products: [],
      title: 'Agent Hub',
      description:
        'View, download, or upload AIOS agents',
      author: 'Vercel',
      author_url: 'https://github.com/vercel',
      author_img: 'https://avatars.githubusercontent.com/u/14985020',
      repo_name: 'vercel/nextjs-subscription-payments',
      repo_url: 'http://localhost:3000/agents',
      vercel_deploy_url:
        'https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel%2Fnextjs-subscription-payments&env=NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,STRIPE_SECRET_KEY&envDescription=Enter%20your%20Stripe%20API%20keys.&envLink=https%3A%2F%2Fdashboard.stripe.com%2Fapikeys&project-name=nextjs-subscription-payments&repository-name=nextjs-subscription-payments&integration-ids=oac_VqOgBHqhEoFTPzGkPd7L0iH6&external-id=https%3A%2F%2Fgithub.com%2Fvercel%2Fnextjs-subscription-payments%2Ftree%2Fmain',
      demo_url: 'https://subscription-payments.vercel.app/',
    },
    {
      type: 'example',
      tags: ['Next.js', 'Vercel'],
      products: [],
      title: 'Agent Chat',
      description:
        'Use and converse with AIOS agents',
      author: 'Supabase',
      author_url: 'https://github.com/supabase',
      author_img: 'https://avatars.githubusercontent.com/u/54469796',
      repo_name: 'vercel/next.js/examples/with-supabase',
      repo_url: (isDevEnv ? 'http://localhost:3000/chat' : 'https://my.aios.foundation/chat'),
      vercel_deploy_url:
        'https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel%2Fnext.js%2Ftree%2Fcanary%2Fexamples%2Fwith-supabase&project-name=nextjs-with-supabase&repository-name=nextjs-with-supabase&demo-title=nextjs-with-supabase&demo-description=This%20starter%20configures%20Supabase%20Auth%20to%20use%20cookies%2C%20making%20the%20user%27s%20session%20available%20throughout%20the%20entire%20Next.js%20app%20-%20Client%20Components%2C%20Server%20Components%2C%20Route%20Handlers%2C%20Server%20Actions%20and%20Middleware.&demo-url=https%3A%2F%2Fdemo-nextjs-with-supabase.vercel.app%2F&external-id=https%3A%2F%2Fgithub.com%2Fvercel%2Fnext.js%2Ftree%2Fcanary%2Fexamples%2Fwith-supabase&demo-image=https%3A%2F%2Fdemo-nextjs-with-supabase.vercel.app%2Fopengraph-image.png&integration-ids=oac_VqOgBHqhEoFTPzGkPd7L0iH6',
      demo_url: 'https://demo-nextjs-with-supabase.vercel.app/',
    }
  ]

const BuiltWithSupabase = () => {
  return (
    <SectionContainer id="examples" className="xl:pt-32">
      <div className="text-center">
        <div className=" text-5xl">Start building in seconds</div>
        <div className="text-2xl pt-6">
          Try out our many features
        </div>

      </div>
      <div className="mt-16 grid grid-cols-12 gap-5">
        {Examples.slice(0, 2).map((example: any, i: number) => {
          return (
            <div
              className={`col-span-12 lg:col-span-6 xl:col-span-6 ${i > 2 && `sm:hidden lg:block`}`}
              key={i}
            >
              <ExampleCard {...example} showProducts />
            </div>
          )
        })}
      </div>
    </SectionContainer>
  )
}

export default BuiltWithSupabase
