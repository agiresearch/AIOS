'use client'

import dynamic from 'next/dynamic'
// import content from '~/data/home/content'
import Layout from '@/components/homepage/DefaultLayout'
import Hero from '@/components/homepage/Hero'
import Logos from '@/components/homepage/logos'

const Products = dynamic(() => import('@/components/homepage/Products'))
// const HeroFrameworks = dynamic(() => import('~/components/Hero/HeroFrameworks'))
// const CustomerStories = dynamic(() => import('components/CustomerStories'))
// const BuiltWithSupabase = dynamic(() => import('components/BuiltWithSupabase'))
// const DashboardFeatures = dynamic(() => import('~/components/DashboardFeatures'))
const TwitterSocialSection = dynamic(() => import('@/components/homepage/TwitterSocialSection'))
// const CTABanner = dynamic(() => import('components/CTABanner/index'))
// const ReactTooltip = dynamic(() => import('react-tooltip'), { ssr: false })

const Index = () => {
  return (
    <div className='w-full h-full flex flex-col pt-12 bg-black text-white'>
       <Hero />
      {/* <Logos /> */}
      <Products />
     
      {/* <TwitterSocialSection /> */}
    </div>
   
    
  )
}

export default Index