from google import genai

client = genai.Client(http_options={"timeout": 60000})
history = []

while True:
	user_text = input("你：")
	if user_text == "退出":
		break

	history.append({"type": "user_input", "content": [{"type": "text", "text": user_text}]})

	reply = client.interactions.create(
		model="gemini-3.5-flash-lite",
		system_instruction="你是一个说话简洁的小红书顾问。",
		input=history,
		store=False,
	)
	answer = reply.output_text
	print("AI:", answer)
	print("（history 里现在有", len(history), "条）")

#	history.append({"type": "model_output", "content": [{"type": "text", "text": answer}]})

