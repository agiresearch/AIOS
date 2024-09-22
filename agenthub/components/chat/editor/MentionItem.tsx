import React, { useEffect, useRef } from "react";

interface MentionItemProps extends React.ComponentPropsWithoutRef<"div"> {
  isActive: boolean;
}

export const MentionItem = ({
  isActive,
  className,
  style,
  ...props
}: MentionItemProps) => {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isActive) {
      ref.current?.scrollIntoView({ block: "nearest" });
    }
  }, [isActive]);

  return (
    <div
      ref={ref}
      className={"mentionsItem" + (className ? ` ${className}` : "")}
      style={{
        backgroundColor: isActive ? "rgba(88, 101, 242, 0.3)" : undefined,
        ...style
      }}
      {...props}
    />
  );
};
