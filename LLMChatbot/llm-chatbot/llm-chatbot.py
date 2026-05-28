from transformers import AutoModelForCausalLM, AutoTokenizer

revision_id = "e5ef2ecae00bee901d5063bc86e1f86eba183702"

model = AutoModelForCausalLM.from_pretrained(
	"microsoft/Phi-3-mini-4k-instruct",
	revision=revision_id,
	device_map="auto",
	torch_dtype="auto",
	trust_remote_code=True,
	)
tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct", revision=revision_id)

from transformers import pipeline

generator = pipeline(
	"text-generation",
	model=model,
	tokenizer=tokenizer,
	return_full_text=False,
	max_new_tokens=500,
	do_sample=False
	)


while True:
    print("+" *50)
    print("What do you want?")
    user_input = input("\033[92mType a question, or pass a file://, or X to exit: \033[0m")
    if user_input in ['X', 'x']:
        print("Exiting.")
        break
    else:
        prompt = user_input
        if user_input.startswith("file://"):
            with open(user_input[7:], 'r') as file:  # Skip 'file://' prefix
                prompt = file.read()
        print("+" *50)
        print("\033[95mPrompt: \033[0m" + prompt)
        print("+" *50)
        messages = [{"role":"user", "content": prompt}]

        output = generator(messages)
        result = output[0]["generated_text"]
        print("\033[94mAI Response: \033[0m" + result)
        print("+" *50)
