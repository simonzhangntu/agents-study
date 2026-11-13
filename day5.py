from datetime import datetime
from google import genai

client = genai.Client(http_options={"timeout": 60000})
MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 5

def calculator(a, b):
    return a * b


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_file(filename):
    try:
        with open(filename, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "错误：找不到文件 " + filename


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


get_time_tool = {
	"type":"function",
	"name":"get_time",
	"description":"获取当前的日期和时间。用户问现在几点、今天几号时使用。",
	"parameters":{"type":"object","properties":{}},
}

read_file_tool ={
	"type":"function",
	"name":"read_file",
	"description":"读取文件。用户要求读文件时使用。",
	"parameters":{
		"type":"object",
		"properties":{
			"filename":{"type":"string","description":"文件名"},
		},
	"required":["filename"],
	},
}

ALL_TOOLS = [calculator_tool, get_time_tool, read_file_tool]

def run_tool(name, args):
	if name =="calculator":
		return calculator(args["a"], args["b"])
	elif name =="get_time":
		return get_time()
	elif name =="read_file":
		return read_file(args["filename"])
	else:
		return "错误：没有这个工具" + name

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
		model=MODEL, input=history, tools=ALL_TOOLS,store=False
	)

	used_tool = False
	for step in reply.steps:
		history.append(step.model_dump())

		if step.type =="function_call":
			used_tool = True
			print("【调用工具】", step.name, step.arguments)
			result = run_tool(step.name, step.arguments)
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