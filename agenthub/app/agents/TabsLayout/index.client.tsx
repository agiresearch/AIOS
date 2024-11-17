'use client'

import { useState, useEffect } from 'react'
import classNames from 'classnames'
import { AgentTabList } from '../const'
import { DatasetsTabItem, AgentItem } from '../type'
import { ApplySVG, ExitSVG } from '@/ui/svgs'
import { baseUrl } from '@/lib/env'

export default function LeftTabsLayout() {
  const [currentTab, setCurrentTab] = useState<DatasetsTabItem>('Academic')
  const [agents, setAgents] = useState<AgentItem[]>([])
  const isAddFilterModalDisplay = false;

  useEffect(() => {
    const fetchAgents = async () => {
      const res = await fetch(`${baseUrl}/api/get_all_agents/light`, { cache: 'no-store' });
      const data = await res.json();
      setAgents(Object.values(data));
    };

    fetchAgents();
  }, []);

  const onTabClick = (tabName: DatasetsTabItem) => {
    setCurrentTab(tabName)
  }

  // 根据当前选中的分类过滤 agents
  const filteredAgents = agents.filter(agent => {
    const name = agent.name.toLowerCase();
    switch(currentTab) {
      case 'Academic':
        return name.includes('academic') || name.includes('math');
      case 'Creative':
        return name.includes('creator') || name.includes('designer') || name.includes('composer');
      case 'Lifestyle':
        return name.includes('therapist') || name.includes('trainer') || name.includes('mixologist');
      case 'Entertainment':
        return name.includes('entertainment') || name.includes('game');
      default:
        return true;
    }
  });

  return (
    <section
      className={classNames(
        'pt-8 border-gray-100 bg-white lg:static lg:px-0 lg:col-span-4 xl:col-span-3 lg:border-r lg:bg-gradient-to-l from-gray-50-to-white',
        isAddFilterModalDisplay ? 'fixed overflow-y-auto overflow-x-hidden z-40 inset-0 !px-4 !pt-4' : ''
      )}
    >
      <div className="mb-4 flex items-center justify-between lg:hidden">
        <h3 className="text-base font-semibold">Agent Categories</h3>
        <button className="text-xl" type="button">
          <ExitSVG />
        </button>
      </div>
      <ul className="flex gap-1 text-sm flex-wrap mt-1.5 mb-5">
        {AgentTabList.map((tabName, index) => (
          <li key={index}>
            <button
              className={classNames(
                'flex items-center whitespace-nowrap rounded-lg px-3 py-1.5',
                currentTab === tabName
                  ? 'bg-black text-white dark:bg-gray-800'
                  : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-900 dark:hover:text-gray-300'
              )}
              onClick={() => {
                onTabClick(tabName)
              }}
            >
              {tabName}
            </button>
          </li>
        ))}
      </ul>
      
      <div className="mb-3">
        <div className="flex flex-col space-y-2">
          {filteredAgents.map((agent) => (
            <a 
              key={agent.id} 
              className="text-sm text-gray-600 hover:text-black hover:bg-gray-100 rounded-lg px-3 py-2"
              href={`/agents/${agent.name}+${agent.version}`}
            >
              {agent.name}
            </a>
          ))}
        </div>
      </div>
    </section>
  )
}
