import { Calculator, LucideProps } from "lucide-react";

export const AgentMapping = {
    story: {
        displayName: 'Story Agent',
        icon: <Calculator />,
        color: 'red'
    },
    math: {
        displayName: 'Math Agent',
        icon: <Calculator color={'green'} />,
        color: 'green'
    }
}