from google import genai

client = genai.Client(http_options={"timeout": 60000})
MODEL = "gemini-3.5-flash-lite"


def calculator(a, b):
	return a*b


calculator_tool ={
	"type":"function",
	"name":"calculator",
	"description":"计算两个数相乘的结果。需要做乘法时使用。",
	"parameters":{
		"type":"object",
		"properties":{
			"a":{"type":"number","description":"第一个数"},
			"b":{"type":"number","description":"第二个数"},
		},
	"required":["a", "b"],
	},
}

history = [
    {"type": "user_input", "content": [{"type": "text", "text": "你好，今天心情不错"}]}
]


reply = client.interactions.create(
	model=MODEL, input=history, tools=[calculator_tool],store=False
)

for step in reply.steps:
	print("【模型返回】",step.type)
	history.append(step.model_dump())

	if step.type == "function_call":
		print("【模型想调用】",step.name, step.arguments)

		result = calculator(step.arguments["a"],step.arguments["b"])
		print("【程序执行结果】",result)

		history.append({
			"type":"function_result",
			"name":step.name,
			"call_id":step.id,
			"result":str(result),
			})

reply2 = client.interactions.create(
	model=MODEL, input=history, tools=[calculator_tool],store=False
)

print("【最终回答】",reply2.output_text)