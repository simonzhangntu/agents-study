from google import genai

client = genai.Client(http_options={"timeout": 60000})
MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 5

def calculator(a, b):
	return a * b

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

question = input("你的问题：")
history = [
	{"type":"user_input","content":[{"type":"text","text":question}]}
]

step_count = 0
finished = False

while step_count < MAX_STEPS:
	step_count = step_count + 1
	print("\n=====第", step_count, "轮 =====")

	reply = client.interactions.create(
		model=MODEL, input=history, tools=[calculator_tool],store=False
	)

	used_tool = False
	for step in reply.steps:
		history.append(step.model_dump())

		if step.type =="function_call":
			used_tool = True
			print("【调用工具】", step.name, step.arguments)
			result = calculator(step.arguments["a"],step.arguments["b"])
			print("【工具结果】",result)
			history.append({
				"type":"function_result",
				"name":step.name,
				"call_id":step.id,
				"result":str(result),
			})

	if not used_tool:
		print("【最终回答】:", reply.output_text)
		finished = True
		break

if not finished:
	print("⚠️ 已经跑了", MAX_STEPS, "轮还没结束，强制停止")