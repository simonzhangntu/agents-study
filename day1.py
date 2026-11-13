from google import genai

client = genai.Client(http_options={"timeout": 60000})

reply = client.interactions.create(
	model="gemini-3.5-flash-lite",
	system_instruction="你是一个毒舌的美食博主。",
	input="用一句话告诉我，什么是AI agent?",
)

print(reply.output_text)

reply2 = client.interactions.create(
    model="gemini-3.5-flash-lite",
    input="把你刚才那句话再说短一点",
)
print(reply2.output_text)