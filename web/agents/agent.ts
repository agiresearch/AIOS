import Groq from 'groq-sdk';
import { groq_token } from "./constants";

export type AgentType = 'decisive' | 'conversational' | 'laborious';


export default class Agent {
    private groq = new Groq({
        apiKey: groq_token,
        dangerouslyAllowBrowser: true
    });

    private name: string;
    
    constructor(name: string) {
        this.name = name;
    }

    async inference(system: string, prompt: string, json: boolean, schema?: string) {
        let response;

        if (json && schema) {
            response = await this.groq.chat.completions.create({
                messages: [
                    {
                        role: 'system',
                        content: `${system}. \n You output results in JSON. Make sure to follow the JSON schema ${schema}`,
                    },
                    {
                        role: "user",
                        content: `${prompt}`,
                    },
                ],
                model: "mixtral-8x7b-32768",
                response_format: { "type": "json_object" }
            });

            return JSON.parse(response!.choices[0]!.message!.content!)
        } else {
            response = await this.groq.chat.completions.create({
                messages: [
                    {
                        role: 'system',
                        content: `${system}.`,
                    },
                    {
                        role: "user",
                        content: `${prompt}`,
                    },
                ],
                model: "llama3-8b-8192",
            });

            return response!.choices[0]!.message!.content!
        }
    }
}
