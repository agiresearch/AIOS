import { BookOpen } from 'lucide-react'
import { useRouter } from 'next/router'
// import Button from '../ui/Button'
import SectionContainer from '@/components/homepage/SectionContainer'
import { Button, Link } from '@nextui-org/react'

const Hero = () => {
  const router = useRouter()

  return (
    <div className="relative -mt-[65px]">
      <SectionContainer className="pt-8 md:pt-16 overflow-hidden">
        <div className="relative">
          <div className="mx-auto">
            <div className="mx-auto max-w-2xl lg:col-span-6 lg:flex lg:items-center justify-center text-center">
              <div className="relative z-10 lg:h-auto pt-[90px] lg:pt-[90px] lg:min-h-[300px] flex flex-col items-center justify-center sm:mx-auto md:w-3/4 lg:mx-0 lg:w-full gap-4 lg:gap-8">
                <div className="flex flex-col items-center">
                  <h1 className="text-foreground text-4xl sm:text-5xl sm:leading-none lg:text-7xl">
                    <span className="block text-foreground">Build in a weekend</span>
                    <span className="text-brand block md:ml-0">Scale to billions</span>
                  </h1>
                  <p className="pt-2 text-foreground my-3 text-sm sm:mt-5 lg:mb-0 sm:text-base lg:text-lg">
                    Supabase is an open source Firebase alternative.{' '}
                    <br className="hidden md:block" />
                    Start your project with a Postgres database, Authentication, instant APIs, Edge
                    Functions, Realtime subscriptions, Storage, and Vector embeddings.
                  </p>
                </div>
                <div className="flex items-center gap-2">

                  <Link as={Button} size="md" type="button" href="https://supabase.com/dashboard">
                  Start your project
                  </Link>
                  <Link as={Button} size="md" type="button" href="/contact/sales">
                    Request a demo
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </SectionContainer>
    </div>
  )
}

export default Hero