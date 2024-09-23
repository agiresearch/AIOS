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

interface MentionListProps extends SuggestionProps {}

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
        axios({
          url: "http://localhost:8000/get_all_agents",
          method: "get",
        }).then((res) => {
          if (!isMounted.current) return;
          setPeople(res.data.agents ?? []);
        });
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
      placement: "bottom-start"
    });

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
