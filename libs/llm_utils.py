### LLM utils 

#%%
import tiktoken
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")


# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

def get_oai_fees(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    if model_name.startswith("gpt-4-32k"):
        model_name = "gpt-4-32k"
    elif model_name.startswith("gpt-4-1106"):
        model_name = "gpt-4-1106-preview"
    elif model_name.startswith("gpt-4"):
        model_name = "gpt-4"
    elif model_name.startswith("gpt-3.5-turbo-16k"):
        model_name = "gpt-3.5-turbo-16k"
    elif model_name.startswith("gpt-3.5-turbo-1106"):
        model_name = "gpt-3.5-turbo-1106"
    elif model_name.startswith("gpt-3.5-turbo"):
        model_name = "gpt-3.5-turbo"
    else:
        raise ValueError(f"Unknown model name {model_name}")
    if model_name not in OAI_PRICE_DICT:
        return -1
    fee = (OAI_PRICE_DICT[model_name]["prompt"] * prompt_tokens + OAI_PRICE_DICT[model_name]["completion"] * completion_tokens) / 1000
    # print (f"Model name used for billing: {model_name} \n{fee}")
    
    return fee

OAI_PRICE_DICT = {
    "gpt-4": {
        "prompt": 0.03,
        "completion": 0.06
    },
    "gpt-4-32k": {
        "prompt": 0.06,
        "completion": 0.12
    },
    "gpt-4-1106-preview": {
        "prompt": 0.01,
        "completion": 0.03
    },
    "gpt-3.5-turbo": {
        "prompt": 0.0015,
        "completion": 0.002
    },
    "gpt-3.5-turbo-16k": {
        "prompt": 0.003,
        "completion": 0.004
    },
    "gpt-3.5-turbo-1106": {
        "prompt": 0.001,
        "completion": 0.002
    }
}

#%%
if __name__ == "__main__":
    print(tiktoken_len('a test sentence, macroeconomist'))
# %%
