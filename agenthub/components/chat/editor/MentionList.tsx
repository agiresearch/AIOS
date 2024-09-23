'use client'

import { SuggestionKeyDownProps, SuggestionProps } from "@tiptap/suggestion";
import axios from "axios";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useState
} from "react";
import { createPortal } from "react-dom";
import { usePopper } from "react-popper";
import { MentionItem } from "./MentionItem";
import type { NamedAgent } from "./types";
import { useIsMounted } from "./useIsMounted";
import { baseUrl } from "@/lib/env";

interface MentionListProps extends SuggestionProps { }

interface MentionListActions {
  onKeyDown: (props: SuggestionKeyDownProps) => void;
}

export const MentionList = forwardRef<MentionListActions, MentionListProps>(
  ({ clientRect, command, query }, ref) => {
    const referenceEl = useMemo(
      () => (clientRect ? { getBoundingClientRect: clientRect } : null),
      [clientRect]
    );

    const isMounted = useIsMounted();
    const [people, setPeople] = useState<NamedAgent[]>([]);

    useEffect(() => {
      console.log(people);
    }, [people])
    // useEffect(() => {
    //   axios({
    //     url: "http://localhost:3000",
    //     method: "get",
    //     params: { search: query }
    //   }).then((res) => {
    //     if (!isMounted.current) return;
    //     setPeople(res.data.results ?? []);
    //   });
    // }, [query, isMounted]);

    useEffect(() => {
      // axios({
      //   url: 'https://agenthub-lite.vercel.app/api/proxy',
      //   method: "POST",
      //   data: {
      //     type: 'GET',
      //     url: "http://35.232.56.61:8000/get_all_agents/"
      //   }
      // }).then((res) => {
      //   // console.log('heyy')
      //   // if (!isMounted.current) return;
      //   // console.log(res.data, 'ress');
      //   setPeople(res.data.agents ?? []);
      // });

      const _ = async () => {
        const response = await axios.post(`${baseUrl}/api/proxy`, {
          type: 'GET',
          url: "http://35.232.56.61:8000/get_all_agents"
        });

        // console.log(response.data, 'response');
        setPeople(response.data.agents ?? []);
      }

      _();

    }, [query, isMounted]);

    const handleCommand = (index: any) => {
      const selectedPerson = people[index];
      command({ id: selectedPerson.id, label: selectedPerson.display });
    };

    const [hoverIndex, setHoverIndex] = useState(0);
    useImperativeHandle(ref, () => ({
      onKeyDown: ({ event }) => {
        const { key } = event;

        if (key === "ArrowUp") {
          setHoverIndex((prev) => {
            const beforeIndex = prev - 1;
            return beforeIndex >= 0 ? beforeIndex : 0;
          });
          return true;
        }

        if (key === "ArrowDown") {
          setHoverIndex((prev) => {
            const afterIndex = prev + 1;
            const peopleCount = people.length - 1;
            return afterIndex < peopleCount ? afterIndex : peopleCount;
          });
          return true;
        }

        if (key === "Enter") {
          handleCommand(hoverIndex);
          return true;
        }

        return false;
      }
    }));

    const [el, setEl] = useState<HTMLDivElement | null>(null);
    //@ts-ignore
    const { styles, attributes } = usePopper(referenceEl, el, {
      placement: "top-start"
    });

    const [_isMounted, set_IsMounted] = useState(false)

    useEffect(() => {
      set_IsMounted(true)
    }, [])

    if (!_isMounted) {
      return null // or a loading placeholder
    }

    return createPortal(
      <div
        ref={setEl}
        className="mentionsContainer"
        style={styles.popper}
        {...attributes.popper}
      >
        {people.map((person, index) => (
          <MentionItem
            key={person.id}
            isActive={index === hoverIndex}
            onMouseEnter={() => setHoverIndex(index)}
            onClick={() => handleCommand(index)}
          >
            {person.display}
          </MentionItem>
        ))}
      </div>,
      document.body
    );
  }
);


MentionList.displayName = 'MentionList';