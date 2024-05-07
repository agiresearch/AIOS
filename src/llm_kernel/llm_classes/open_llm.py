import torch
from .constant import MODEL_CLASS
from .base_llm import BaseLLMKernel
import time
from transformers import AutoTokenizer

class OpenLLM(BaseLLMKernel):

    def load_llm_and_tokenizer(self) -> None:
        self.max_gpu_memory = self.convert_map(self.max_gpu_memory)

        self.model = MODEL_CLASS[self.model_type].from_pretrained(
            self.model_name,
            device_map="auto",
            max_memory=self.max_gpu_memory
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
        )
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def process(self,
                llm_request,
                temperature=0.0) -> None:
        prompt = llm_request.prompt

        pid = "-".join([llm_request.agent_name, str(llm_request.agent_id), str(llm_request.step)])

        if self.context_manager.check_restoration(pid):
            restored_context = self.context_manager.gen_recover(
                pid
            )
            start_idx = restored_context["start_idx"]
            beams = restored_context["beams"]
            beam_scores = restored_context["beam_scores"]
            beam_attention_masks = restored_context["beam_attention_masks"]

            outputs = self.generate(
                search_mode = "beam_search",
                beam_size = 1,
                beams = beams,
                beam_scores = beam_scores,
                beam_attention_masks = beam_attention_masks,
                max_new_tokens = self.MAX_NEW_TOKENS,
                start_idx = start_idx,
                timestamp = llm_request.get_time_limit()
            )
        else:
            prompt = llm_request.prompt
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
                start_idx = 0,
                timestamp = llm_request.get_time_limit()
            )

        output_ids = outputs["result"]

        prompt = llm_request.prompt
        result = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        result = result[len(prompt)+1: ]

        if outputs["finished_flag"]: # finished flag is set as True

            if self.context_manager.check_restoration(
                pid):
                self.context_manager.clear_restoration(
                    pid
                )
            # agent_process.set_response(result)
            llm_request.set_status("done")
            return result

        else:

            self.context_manager.gen_snapshot(
                pid,
                context = {
                    "start_idx": outputs["start_idx"],
                    "beams": outputs["beams"],
                    "beam_scores": outputs["beam_scores"],
                    "beam_attention_masks": outputs["beam_attention_masks"]
                }
            )
            llm_request.set_status("suspend")

        return result

    def generate(self,
                 input_ids: torch.Tensor = None,
                 attention_masks: torch.Tensor = None,
                 beams: torch.Tensor = None,
                 beam_scores: torch.Tensor = None,
                 beam_attention_masks: torch.Tensor = None,
                 beam_size: int = None,
                 max_new_tokens: int = None,
                 search_mode: str = None,
                 start_idx: int = 0,
                 timestamp: int = None
                 ):
        if search_mode == "beam_search":
            output_ids = self.beam_search(
                input_ids = input_ids,
                attention_masks = attention_masks,
                beam_size = beam_size,
                beams = beams,
                beam_scores = beam_scores,
                beam_attention_masks = beam_attention_masks,
                max_new_tokens = max_new_tokens,
                start_idx = start_idx,
                timestamp = timestamp
            )
            return output_ids
        else:
            return NotImplementedError

    def generate(self,
                 input_ids: torch.Tensor = None,
                 attention_masks: torch.Tensor = None,
                 beams: torch.Tensor = None,
                 beam_scores: torch.Tensor = None,
                 beam_attention_masks: torch.Tensor = None,
                 beam_size: int = None,
                 max_new_tokens: int = None,
                 search_mode: str = None,
                 start_idx: int = 0,
                 timestamp: int = None
                 ):
        if search_mode == "beam_search":
            output_ids = self.beam_search(
                input_ids = input_ids,
                attention_masks = attention_masks,
                beam_size = beam_size,
                beams = beams,
                beam_scores = beam_scores,
                beam_attention_masks = beam_attention_masks,
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
                    beams=None,
                    beam_scores=None,
                    beam_attention_masks=None,
                    beam_size: int = None,
                    max_new_tokens: int = None,
                    start_idx: int = 0,
                    timestamp: int = None
                    ):

        if beams is None or beam_scores is None or beam_attention_masks is None:
            beams = input_ids.repeat(beam_size, 1)
            beam_attention_masks = attention_masks.repeat(beam_size, 1)
            beam_scores = torch.zeros(beam_size, device=self.eval_device)

        start_time = time.time()

        finished_flag = False

        idx = start_idx

        for step in range(start_idx, max_new_tokens):
            with torch.no_grad():
                # Obtain logits for the last tokens across all beams
                outputs = self.model(beams, attention_mask=beam_attention_masks)
                next_token_logits = outputs.logits[:, -1, :]

                # Apply softmax to convert logits to probabilities
                next_token_probs = torch.softmax(next_token_logits, dim=-1)

            # Calculate scores for all possible next tokens for each beam
            next_token_scores = beam_scores.unsqueeze(-1) + torch.log(next_token_probs)

            # Flatten to treat the beam and token dimensions as one
            next_token_scores_flat = next_token_scores.view(-1)

            # Select top overall scores to find the next beams
            top_scores, top_indices = torch.topk(next_token_scores_flat, beam_size, sorted=True)

            # Determine the next beams and their corresponding tokens
            beam_indices = top_indices // next_token_probs.size(1)  # Find which beam the top tokens came from
            token_indices = top_indices % next_token_probs.size(1)  # Find which token within the beam was selected

            # Update beams, scores, and attention masks
            beams = torch.cat([beams[beam_indices], token_indices.unsqueeze(-1)], dim=-1)
            beam_attention_masks = torch.cat([beam_attention_masks[beam_indices], torch.ones_like(token_indices).unsqueeze(-1)], dim=-1)
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
            "beam_attention_masks": beam_attention_masks,
            "result": best_beam
        }

        return outputs
