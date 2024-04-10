import torch

import sys

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)

model_class = {
    "causal_lm": AutoModelForCausalLM,
}

from openai import OpenAI

from src.utils.utils import get_from_env

import os

import json

import re

import time

from src.agents.agent_process import AgentProcess

from src.context.simple_context import SimpleContextManager

class LLMKernel:
    def __init__(self, llm_name: str, max_gpu_memory: dict = None, eval_device: str = None, max_new_tokens: int = 256):
        print("Initialize AIOS powered by LLM: {}".format(llm_name))
        self.config = self.load_config(llm_name)
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device

        self.load_llm_and_tokenizer()
        self.MAX_NEW_TOKENS = max_new_tokens

        self.context_manager = SimpleContextManager()

        print("AIOS LLM successfully loaded. ")

    def convert_map(self, map: dict) -> dict:
        new_map = {}
        for k,v in map.items():
            new_map[int(k)] = v
        return new_map

    def load_config(self, llm_name):
        # print(os.getcwd())
        config_file = os.path.join(os.getcwd(), "src", "llms", "llm_config/{}.json".format(llm_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def load_llm_and_tokenizer(self): # load model from config
        open_sourced = self.config["open_sourced"]
        self.model_type = self.config["model_type"]
        self.model_name = self.config["model_name"]

        if open_sourced:
            self.max_gpu_memory = self.convert_map(self.max_gpu_memory)
            hf_token = self.config["hf_token"] if "hf_token" in self.config.keys() else None
            cache_dir = self.config["cache_dir"] if "cache_dir" in self.config.keys() else None

            self.model = model_class[self.model_type].from_pretrained(
                self.model_name,
                use_auth_token = hf_token,
                cache_dir = cache_dir,
                # torch_dtype=torch.float16,
                # load_in_8bit = True,
                device_map="auto",
                max_memory = self.max_gpu_memory
            )
            # self.model = self.model.to(self.eval_device)
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_auth_token = hf_token,
                cache_dir = cache_dir
            )
            # print(f"EOS token id: {self.model.config.eos_token_id}")
            self.tokenizer.pad_token_id = self.model.config.eos_token_id
            # print(self.tokenizer.pad_token_id)
        else:
            if re.search(r'gpt', self.model_name, re.IGNORECASE):
                self.model = OpenAI()
                self.tokenizer = None
            if self.model_name == "gemini-pro":
                try:
                    import google.generativeai as genai
                    gemini_api_key = get_from_env("GEMINI_API_KEY")
                    genai.configure(api_key=gemini_api_key)
                    self.model = genai.GenerativeModel(self.model_name)
                    self.tokenizer = None
                except ImportError:
                    raise ImportError(
                        "Could not import google.generativeai python package. "
                        "Please install it with `pip install google-generativeai`."
                    )
            elif self.model_name.startswith("bedrock"):
                try:
                    from langchain_community.chat_models import BedrockChat
                    model_id = self.model_name.split("/")[-1]
                    self.model = BedrockChat(
                        model_id=model_id,
                        model_kwargs={
                            'temperature': 0.0
                        }
                    )
                except ModuleNotFoundError as err:
                    raise err
                except ImportError:
                    raise ImportError(
                        "Could not import langchain_community python package. "
                        "Please install it with `pip install langchain_community`."
                    )
            else:
                return NotImplementedError

    def address_request(self,
            agent_process: AgentProcess
        ):
        # The pattern looks for 'gpt', 'claude', or 'gemini', ignoring case (re.IGNORECASE)
        closed_model_pattern = r'gpt|claude|gemini'

        if re.search(closed_model_pattern, self.model_name, re.IGNORECASE):
            return self.closed_llm_process(
                agent_process
            )
        else:
            return self.open_llm_process(
                agent_process
            )

    def closed_llm_process(self,
            agent_process,
            temperature=0.0
        ):
        if re.search(r'gemini', self.model_name, re.IGNORECASE):
            outputs = self.gemini_process(agent_process, temperature=temperature)
            return outputs
        elif re.search(r'gpt', self.model_name, re.IGNORECASE):
            return self.gpt_process(agent_process, temperature=temperature)
        elif self.model_name.startswith("bedrock") and \
             re.search(r'claude', self.model_name, re.IGNORECASE):
            return self.bedrock_process(agent_process, temperature=temperature)
        else:
            return NotImplementedError

    def gemini_process(self,
            agent_process: AgentProcess,
            temperature=0.0
        ):
        prompt = agent_process.prompt
        outputs = self.model.generate_content(
            prompt
        )
        # print(outputs)
        try:
            return outputs.candidates[0].content.parts[0].text
        except IndexError:
            return f"{self.model_name} can not generate a valid result, please try again"

    def gpt_process(self,
            agent_process:AgentProcess,
            temperature=0.0
        ):
        prompt = agent_process.prompt,
        response = self.model.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        time.sleep(2) # set according to your request per minite
        return response.choices[0].message.content

    def bedrock_process(self,
            prompt,
            temperature=0.0
        ):
        from langchain_core.prompts import ChatPromptTemplate
        chat_template = ChatPromptTemplate.from_messages([
            ("user", f"{prompt}")
        ])
        messages = chat_template.format_messages(prompt=prompt)
        self.model.model_kwargs['temperature'] = temperature
        response = self.model(messages)
        return response.content

    def generate(self,
            input_ids: torch.Tensor,
            attention_masks: torch.Tensor = None,
            beam_size: int = None,
            max_new_tokens: int = None,
            search_mode: str = None,
            start_idx: int = 0,
            timestamp: int = None
        ):
        if search_mode == "beam_search":
            output_ids = self.beam_search(
                input_ids = input_ids,
                attention_mask = attention_masks,
                beam_size = beam_size,
                max_new_tokens = max_new_tokens,
                start_idx = start_idx,
                timestamp = timestamp
            )
            return output_ids
        else:
            return NotImplementedError

    def beam_search(self,
            input_ids: torch.Tensor = None,
            attention_masks: torch.Tensor = None,
            beams = None,
            beam_attention_masks = None,
            beam_size: int = None,
            max_new_tokens: int = None,
            start_idx: int = 0,
            timestamp: int = None
        ):
        # num_sequences = input_ids.shape[0]
        if beams is not None and beam_attention_masks is not None:
            beams = beams
            beam_scores = beam_scores
            beam_attention_masks = beam_attention_masks

        else:
            beams = [input_ids.clone() for _ in range(beam_size)]
            beam_scores = torch.zeros(beam_size, device=self.eval_device)
            beam_attention_masks = [attention_masks.clone() for _ in range(beam_size)]

        start_time = time.time()

        finished_flag = False

        idx = start_idx

        for step in range(start_idx, max_new_tokens):
            candidate_beams = []
            candidate_scores = []
            candidate_attention_masks = []

            for beam, score, beam_attention_mask in zip(beams, beam_scores, beam_attention_masks):
                with torch.no_grad():
                    outputs = self.model(
                        beam,
                        attention_mask=beam_attention_mask
                    )
                    next_token_logits = outputs.logits[:, -1, :]
                    next_token_probs = torch.softmax(next_token_logits, dim=-1)

                top_probs, top_ids = torch.topk(next_token_probs, beam_size)

                for prob, token_id in zip(top_probs[0], top_ids[0]):
                    new_beam = torch.cat((beam, token_id.unsqueeze(0).unsqueeze(0)), dim=1)
                    new_score = score + torch.log(prob)
                    new_attention_mask = torch.cat((beam_attention_mask, torch.ones((1, 1), device=self.eval_device)), dim=1)

                    candidate_beams.append(new_beam)
                    candidate_scores.append(new_score)
                    candidate_attention_masks.append(new_attention_mask)

            candidate_scores = torch.stack(candidate_scores)
            top_beam_indices = torch.topk(candidate_scores, beam_size).indices
            beams = [candidate_beams[i] for i in top_beam_indices]
            beam_scores = candidate_scores[top_beam_indices]
            beam_attention_masks = [candidate_attention_masks[i] for i in top_beam_indices]

            cur_time = time.time()
            if timestamp is not None and cur_time - start_time >= timestamp:
                idx = step
                break

            # Break if all beams end with the end-of-sequence token
            if all(beam[-1, -1].item() == self.tokenizer.eos_token_id for beam in beams):
                idx = max_new_tokens
                finished_flag = True
                break

        if finished_flag:
            best_beam_idx = beam_scores.argmax().item()

            best_beam = beams[best_beam_idx]

            outputs = {
                "finished_flag": finished_flag,
                "start_idx": idx,
                "beams": beams,
                "beam_scores": beam_scores,
                "beam_attention_masks": beam_attention_masks,
                "final_result": best_beam
            }
        else:
            outputs = {
                "finished_flag": finished_flag,
                "start_idx": idx,
                "beams": beams,
                "beam_scores": beam_scores,
                "beam_attention_masks": beam_attention_masks,
                "final_result": None
            }

        return outputs

    def open_llm_process(self,
            agent_process: AgentProcess,
            temperature=0.0
        ):
        status = agent_process.get_status()

        agent_process.set_status("executing")
        self.logger.info(f"[{agent_process.agent_name}] is executing.")
        agent_process.set_start_time(time.time())

        if self.context_manager.check_restoration(agent_process.get_pid()):
            restored_context = self.context_manager.gen_recover(
                agent_process.get_pid()
            )
            start_idx = restored_context["start_idx"]
            beams = restored_context["beams"]
            beam_scores = restored_context["beam_scores"]
            beam_attention_masks = restored_context["beam_attention_masks"]

            outputs = self.generate(
                input_ids = input_ids,
                attention_masks = attention_masks,
                search_mode = "beam_search",
                beam_size = 1,
                beams = beams,
                beam_scores = beam_scores,
                beam_attention_mask = beam_attention_masks,
                max_new_tokens = self.MAX_NEW_TOKENS,
                start_idx = start_idx,
                timestamp = agent_process.get_time_limit()
            )

        else:
            prompt = agent_process.prompt
            input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
            attention_masks = input_ids != self.tokenizer.pad_token_id
            input_ids = input_ids.to(self.eval_device)
            attention_masks = attention_masks.to(self.eval_device)

            outputs = self.generate(
                input_ids = input_ids,
                attention_masks = attention_masks,
                search_mode = "beam_search",
                beam_size = 1,
                max_new_tokens=self.MAX_NEW_TOKENS,
                start_idx = start_idx,
                timestamp = agent_process.get_time_limit()
            )

        if outputs["finished_flag"] and outputs["final_result"] is not None: # finished flag is set as True
            output_ids = outputs["final_result"]
            result = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            result = result[len(prompt)+1: ]

            agent_process.set_response(result)
            agent_process.set_status("done")

        else:
            agent_process.set_status("suspending")
            self.context_manager.gen_snapshot(
                pid = agent_process.get_pid(),
                context = {
                    "start_idx": outputs["start_idx"],
                    "beams": outputs["beams"],
                    "beam_scores": outputs["beam_scores"],
                    "beam_attention_masks": outputs["beam_attention_masks"]
                }
            )
        agent_process.set_end_time(time.time())
