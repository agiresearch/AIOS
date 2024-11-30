# Run models from huggingface using the transformers library

import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM

from aios.llm_core.cores.base import BaseLLM

from cerebrum.llm.communication import Response

from aios.utils import get_from_env

import re


class HfNativeLLM(BaseLLM):
    def __init__(
        self,
        llm_name: str,
        max_gpu_memory: dict = None,
        eval_device: str = "cuda:0",
        max_new_tokens: int = 256,
        log_mode: str = "console",
        use_context_manager: bool = False,
    ):
        super().__init__(
            llm_name,
            max_gpu_memory,
            eval_device,
            max_new_tokens,
            log_mode,
            use_context_manager,
        )

    def load_llm_and_tokenizer(self) -> None:
        self.max_gpu_memory = self.convert_map(self.max_gpu_memory)
        self.auth_token = get_from_env("HF_AUTH_TOKENS")

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            max_memory=self.max_gpu_memory,
            use_auth_token=self.auth_token,
        )
        # self.model = self.model.to(self.eval_device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, use_auth_token=self.auth_token
        )
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def address_syscall(self, llm_syscall, temperature=0.0) -> None:
        llm_syscall.set_status("executing")
        llm_syscall.set_start_time(time.time())
        self.logger.log(
            f"{llm_syscall.agent_name} is switched to executing.\n", level="executing"
        )
        messages = llm_syscall.query.messages
        tools = llm_syscall.query.tools
        message_return_type = llm_syscall.query.message_return_type

        if self.use_context_manager:
            if self.context_manager.check_restoration(llm_syscall.get_pid()):
                restored_context = self.context_manager.gen_recover(
                    llm_syscall.get_pid()
                )
                start_idx = restored_context["start_idx"]
                beams = restored_context["beams"]
                beam_scores = restored_context["beam_scores"]
                beam_attention_mask = restored_context["beam_attention_mask"]

                outputs = self.llm_generate(
                    search_mode="beam_search",
                    beam_size=1,
                    beams=beams,
                    beam_scores=beam_scores,
                    beam_attention_mask=beam_attention_mask,
                    max_new_tokens=self.max_new_tokens,
                    start_idx=start_idx,
                    timestamp=llm_syscall.get_time_limit(),
                )
            else:
                if tools:
                    messages = self.tool_calling_input_format(messages, tools)

                prompt = self.tokenizer.apply_chat_template(messages, tokenize=False)

                input_ids = self.tokenizer.encode(prompt, return_tensors="pt")

                attention_mask = input_ids != self.tokenizer.pad_token_id
                input_ids = input_ids.to(self.eval_device)
                attention_mask = attention_mask.to(self.eval_device)

                outputs = self.llm_generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    search_mode="beam_search",
                    beam_size=1,
                    max_new_tokens=self.max_new_tokens,
                    start_idx=0,
                    timestamp=llm_syscall.get_time_limit(),
                )
                # TODO temporarily
                outputs["result"] = outputs["result"][input_ids.shape[-1] :]
            # output_ids = outputs
            # print(output_ids)
            output_ids = outputs["result"]

            result = self.tokenizer.decode(output_ids, skip_special_tokens=False)

            if outputs["finished_flag"]:  # finished flag is set as True
                if self.context_manager.check_restoration(llm_syscall.get_pid()):
                    self.context_manager.clear_restoration(llm_syscall.get_pid())

                if tools:
                    tool_calls = self.parse_tool_calls(result)
                    response = Response(
                        response_message=None, 
                        tool_calls=tool_calls,
                        finished=True
                    )
                else:
                    response = Response(
                        response_message=result,
                        finished=True
                    )

            else:
                self.context_manager.gen_snapshot(
                    llm_syscall.get_pid(),
                    context={
                        "start_idx": outputs["start_idx"],
                        "beams": outputs["beams"],
                        "beam_scores": outputs["beam_scores"],
                        "beam_attention_mask": outputs["beam_attention_mask"],
                    },
                )
                if message_return_type == "json":
                    result = self.parse_json_format(result)
                response = Response(response_message=result, finished=False)
                
            return response
        else:
            if tools:
                messages = self.tool_calling_input_format(messages, tools)
            messages = self.tool_calling_input_format(messages, tools)
            tokenized_chat = self.tokenizer.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
            )
            tokenized_chat = tokenized_chat.to(self.eval_device)
            input_length = tokenized_chat.shape[1]
            
            outputs = self.model.generate(
                tokenized_chat,
                max_new_tokens=self.max_new_tokens
            )
            
            result = self.tokenizer.decode(
                outputs[0][input_length:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            # print(result)
            tool_calls = self.parse_tool_calls(result)
            if tool_calls:
                response = Response(
                    response_message=None, tool_calls=tool_calls, finished=True
                )
            else:
                if message_return_type == "json":
                    result = self.parse_json_format(result)
                    response = Response(response_message=result, finished=True)
                else:
                    response = Response(response_message=result, finished=True)
            return response

    def llm_generate(
        self,
        input_ids: torch.Tensor = None,
        attention_mask: torch.Tensor = None,
        beams: torch.Tensor = None,
        beam_scores: torch.Tensor = None,
        beam_attention_mask: torch.Tensor = None,
        beam_size: int = None,
        max_new_tokens: int = None,
        search_mode: str = None,
        start_idx: int = 0,
        timestamp: int = None,
    ):
        """only supports beam search generation"""
        if search_mode == "beam_search":
            output_ids = self.beam_search(
                input_ids=input_ids,
                attention_mask=attention_mask,
                beam_size=beam_size,
                beams=beams,
                beam_scores=beam_scores,
                beam_attention_mask=beam_attention_mask,
                max_new_tokens=max_new_tokens,
                start_idx=start_idx,
                timestamp=timestamp,
            )
            return output_ids
        else:
            # TODO: greedy support
            return NotImplementedError

    def beam_search(
        self,
        input_ids: torch.Tensor = None,
        attention_mask: torch.Tensor = None,
        beams=None,
        beam_scores=None,
        beam_attention_mask=None,
        beam_size: int = None,
        max_new_tokens: int = None,
        start_idx: int = 0,
        timestamp: int = None,
    ):
        """
        beam search gets multiple token sequences concurrently and calculates
        which token sequence is the most likely opposed to calculating the
        best token greedily
        """

        if beams is None or beam_scores is None or beam_attention_mask is None:
            beams = input_ids.repeat(beam_size, 1)
            beam_attention_mask = attention_mask.repeat(beam_size, 1)
            beam_scores = torch.zeros(beam_size, device=self.eval_device)

        start_time = time.time()

        finished_flag = False

        idx = start_idx

        for step in range(start_idx, max_new_tokens):
            with torch.no_grad():
                # Obtain logits for the last tokens across all beams
                outputs = self.model(beams, attention_mask=beam_attention_mask)
                next_token_logits = outputs.logits[:, -1, :]

                # Apply softmax to convert logits to probabilities
                next_token_probs = torch.softmax(next_token_logits, dim=-1)

            # Calculate scores for all possible next tokens for each beam
            next_token_scores = beam_scores.unsqueeze(-1) + torch.log(next_token_probs)

            # Flatten to treat the beam and token dimensions as one
            next_token_scores_flat = next_token_scores.view(-1)

            # Select top overall scores to find the next beams
            top_scores, top_indices = torch.topk(
                next_token_scores_flat, beam_size, sorted=True
            )

            # Determine the next beams and their corresponding tokens
            beam_indices = top_indices // next_token_probs.size(
                1
            )  # Find which beam the top tokens came from
            token_indices = top_indices % next_token_probs.size(
                1
            )  # Find which token within the beam was selected

            # Update beams, scores, and attention masks
            beams = torch.cat(
                [beams[beam_indices], token_indices.unsqueeze(-1)], dim=-1
            )
            beam_attention_mask = torch.cat(
                [
                    beam_attention_mask[beam_indices],
                    torch.ones_like(token_indices).unsqueeze(-1),
                ],
                dim=-1,
            )
            beam_scores = top_scores

            # Check for stopping criteria
            if timestamp is not None and time.time() - start_time >= timestamp:
                idx = step
                break

            # Check for completion
            if torch.all(beams[:, -1] == self.tokenizer.eos_token_id):
                idx = step
                finished_flag = True
                break

            if step + 1 == max_new_tokens:
                idx = step
                finished_flag = True
                break

        best_beam_idx = beam_scores.argmax()

        best_beam = beams[best_beam_idx]

        outputs = {
            "finished_flag": finished_flag,
            "start_idx": idx,
            "beams": beams,
            "beam_scores": beam_scores,
            "beam_attention_mask": beam_attention_mask,
            "result": best_beam,
        }

        return outputs
