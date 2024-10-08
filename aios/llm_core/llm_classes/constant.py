# depending on the model type, laod pretrained models
# for example, all our models are casual lms right now
# used in open_llm.py

from transformers import AutoModelForCausalLM

MODEL_CLASS = {
    "causal_lm": AutoModelForCausalLM,
}
