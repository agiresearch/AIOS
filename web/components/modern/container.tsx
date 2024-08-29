import React, { ReactNode, useEffect, useRef } from 'react';

const Container = ({ children }: { children: ReactNode[] }) => {
    const containerRef = useRef<any>(null);
    let priorRef = useRef<any>(null);

    useEffect(() => {
        if (containerRef.current) {
            const container = containerRef.current;
            const lastChild = container.lastElementChild;

            if (lastChild && priorRef.current == null) {
                priorRef.current = lastChild;
            } else if (lastChild && lastChild != priorRef.current) {
                setTimeout(() => {
                    lastChild.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }, 170); // Delay of 100ms
                priorRef.current = lastChild;
            }


        }
    }, [children]);

    return (
        <div ref={containerRef} className="h-[90%] w-full flex flex-col max-h-[92%] overflow-y-auto">
            {children}
        </div>
    );
};

export default Container;