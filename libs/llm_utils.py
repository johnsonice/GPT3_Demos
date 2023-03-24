### LLM utils 

#%%
import tiktoken
tokenizer = tiktoken.get_encoding('p50k_base')


# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)


#%%
if __name__ == "__main__":
    print(tiktoken_len('a test sentence, macroeconomist'))
# %%
