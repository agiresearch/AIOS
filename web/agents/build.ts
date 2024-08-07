import { evaluate } from 'mathjs'
import Agent, { AgentType } from './agent'

export const readSchemaFromObject = (obj: any): string => {
    const schema: Record<string, string> = {};
    
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            schema[key] = obj[key];
        }
    }
    
    return JSON.stringify(schema, null, 2);
}

class AgentBuilder {
    private agents: Record<string, any>;

    constructor() {
        this.agents = {}
    }

    build(name: string, type: AgentType,  system?: string, _schema?: any) {
        const kernel = new Agent(name);

        let system_prompt = '';
        let schema = {};

        switch (type) {
            case 'decisive':
                schema = {
                    isTrue: 'boolean true if statement is true, or false is statement is false'
                }
                system_prompt='You will be given a prompt, and you are to decide if it/its conditions are either true or false.'
            case 'conversational':
                system_prompt = 'Reword the given phrase or statement or text into a conversational manner that sounds like a human.'
            case 'laborious':
                schema = _schema;
                system_prompt=system!
        }

        const agentRun = async (instruct: string) => {
            const result = await kernel.inference(system_prompt, instruct, Object.keys(schema).length === 0 ? false : true, readSchemaFromObject(schema))
            if (type == 'decisive') {
                return result.isTrue
            } else {
                return result
            }
        }

        this.agents[name] = agentRun;
    }

    async run(name: string, prompt: string) {
        const agent = this.agents[name];
        console.log(agent);

        const result = await agent(prompt);

        return result;
    }
}

export const builder = new AgentBuilder();

builder.build('expression_agent', 'laborious', 'You are an agent that structures words problems into numerical math expressions that can be read by MathJS. YOU DO NOT EVALUATE THE PROBLEM OR SOLVE IT, SIMPLY MAKING IT INTO AN EXPRESSION', {
    expression: 'math expression goes here'
})

builder.build('story_agent', 'laborious', 'You are an agent that writes a short story according to the instructions given. Use a maximum of 120 words.', {})


export const ExpressionAgent = async (phrase: string) => {
    const res = await builder.run('expression_agent', phrase)
    return res.expression;
}

export const EvalAgent = (phrase: string) => {
    return evaluate(phrase);
}

export const MathAgent = async (phrase: string) => {
    console.log('here')
    const res = await builder.run('expression_agent', phrase)
    console.log(res.expression)
    console.log(evaluate(res.expression))
    return evaluate(res.expression);
}

export const StoryAgent = async (phrase: string) => {
    const res = await builder.run('story_agent', phrase)
    return res
}

// if (import.meta.url === new URL(import.meta.url).href) {
//     (async function () {
//         // Your main code here
//         const res = await ExpressionAgent('I have 59 chickens and my friend has 32 chickens, how many chickens are there in total?')
//         console.log(`Expression Is: ${res}`);

//         const ans = EvalAgent(res);
//         console.log(`Answer Is: ${ans}`);
//     })();
// }



