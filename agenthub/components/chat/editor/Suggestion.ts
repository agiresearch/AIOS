import { ReactRenderer } from '@tiptap/react'
import tippy from 'tippy.js'

import MentionListV2 from './MentionListV2'
import { baseUrl, serverUrl } from '@/lib/env';
import axios from 'axios';


export default {
  items: async ({ query }: { query: any }) => {
    const response = await axios.post(`${baseUrl}/api/proxy`, {
      type: 'GET',
      url: `${serverUrl}/get_all_agents`,
    });

    console.log(response.data.agents)

    return response.data.agents.map((agent: any) => agent.display)
    // .filter((item: any) => item.toLowerCase().startsWith(query.toLowerCase()))
      // .slice(0, 5)
  },

  render: () => {
    let component: any
    let popup: any

    return {
      onStart: (props: any) => {
        component = new ReactRenderer(MentionListV2, {
          props,
          editor: props.editor,
        })

        if (!props.clientRect) {
          return
        }

        popup = tippy('body', {
          getReferenceClientRect: props.clientRect,
          appendTo: () => document.body,
          content: component.element,
          showOnCreate: true,
          interactive: true,
          trigger: 'manual',
          placement: 'bottom-start',
        })
      },

      onUpdate(props: any) {
        component.updateProps(props)

        if (!props.clientRect) {
          return
        }

        popup[0].setProps({
          getReferenceClientRect: props.clientRect,
        })
      },

      onKeyDown(props: any) {
        if (props.event.key === 'Escape') {
          popup[0].hide()

          return true
        }

        return component.ref?.onKeyDown(props)
      },

      onExit() {
        popup[0].destroy()
        component.destroy()
      },
    }
  },
}