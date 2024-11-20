import { BookOpen } from 'lucide-react'
// import { useRouter } from 'next/router'
// import Button from '../ui/Button'
import SectionContainer from '@/components/homepage/SectionContainer'
import { Button, Link } from '@nextui-org/react'

const Hero = () => {
  // const router = useRouter()

  return (
    <div className="relative -mt-[65px]">
      <SectionContainer className="pt-8 md:pt-16 overflow-hidden">
        <div className="relative">
          <div className="mx-auto">
            <div className="mx-auto max-w-2xl lg:col-span-6 lg:flex lg:items-center justify-center text-center">
              <div className="relative z-10 lg:h-auto pt-[90px] lg:pt-[90px] lg:min-h-[300px] flex flex-col items-center justify-center sm:mx-auto md:w-3/4 lg:mx-0 lg:w-full gap-4 lg:gap-8">
                <div className="flex flex-col items-center">
                  <h1 className="text-foreground text-4xl sm:text-5xl sm:leading-none lg:text-7xl">
                    <span className="text-7xl block text-foreground">AIOS </span>
                    <span className="text-5xl py-2 text-brand block md:ml-0 font-medium">LLM Agent Operating System</span>
                  </h1>
                  <p className="pt-2 text-foreground my-3 text-sm sm:mt-5 lg:mb-0 sm:text-base lg:text-lg">
                  The goal of AIOS is to build a large language model (LLM) agent operating system, which intends to embed large language model into the operating system as the brain of the OS. AIOS is designed to address problems (e.g., scheduling, context switch, memory management, etc.) during the development and deployment of LLM-based agents, for a better ecosystem among agent developers and users.
                  </p>
                </div>
                <div className="flex items-center gap-2">

                  {/* <Link as={Button} size="md" type="button" href="https://supabase.com/dashboard">
                  Get Started
                  </Link> */}
                  <a 
                  href='https://aios-3.gitbook.io/'
                  target='_blank'
                  className='relative justify-center cursor-pointer inline-flex items-center space-x-2 text-center font-regular ease-out duration-200 rounded-md outline-none transition-all outline-0 focus-visible:outline-4 focus-visible:outline-offset-1 border text-foreground bg-getstarted hover:bg-selection border-strong hover:border-stronger focus-visible:outline-brand-600 data-[state=open]:bg-selection data-[state=open]:outline-brand-600 data-[state=open]:border-button-hover text-sm px-4 py-2 h-[38px]'>
                    Read the Docs
                  </a>
                  {/* <Link as={Button} size="md" type="button" href="/contact/sales">
                    Request a demo
                  </Link> */}
                  <a 
                  target='_blank'
                  href='https://github.com/agiresearch/AIOS'
                  className='relative justify-center cursor-pointer inline-flex items-center space-x-2 text-center font-regular ease-out duration-200 rounded-md outline-none transition-all outline-0 focus-visible:outline-4 focus-visible:outline-offset-1 border text-foreground bg-muted hover:bg-selection border-strong hover:border-stronger focus-visible:outline-brand-600 data-[state=open]:bg-selection data-[state=open]:outline-brand-600 data-[state=open]:border-button-hover text-sm px-4 py-2 h-[38px]'>
                    View On Github
                  </a>
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
