from datetime import datetime
import anthropic
import requests

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
MAX_STEPS = 6



def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_note(filename, content):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(content + "\n")
    return "已写入 " + filename


def search_wikipedia(query):
    url = "https://zh.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": 3,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "exlimit": 3,
        "exchars": 500,
        "format": "json",
        "formatversion": 2,
    }

    headers = {"User-Agent": "agents-study/0.1 (learning project)"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
    except Exception as e:
        return "错误：连接不上维基百科（" + str(e) +"）。请告诉用户网络可能有问题，不要编造任何内容。"

    if "query" not in data:
        return "没有找到和“" + query + "”相关的词条。可以换一个更短、更加常见的关键词再搜索一次。"

    result = ""
    for page in data["query"]["pages"]:
        result = result + "【" + page["title"] + "】\n" + page.get("extract", "") + "\n\n"
    return result

get_time_tool = {
    "name": "get_time",
    "description": "获取当前的日期和时间。用户问现在几点、今天几号，或者需要根据时间做判断时使用。",
    "input_schema": {"type": "object", "properties": {}},
}

write_note_tool = {
    "name": "write_note",
    "description": "把一段文字追加到本地文件末尾（不会覆盖原有内容）。用户要求记录、保存、写入笔记时使用。",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "文件名，比如 notes.md"},
            "content": {"type": "string", "description": "要写入的文字"},
        },
        "required": ["filename", "content"],
    },
}


search_wikipedia_tool = {
    "name": "search_wikipedia",
    "description": ("搜索中文维基百科，返回最相关的最多3个词条，每个词条包括一个标题和一段不超过500字的简介。"
    "需要查询概念、人物、历史等百科知识时候调用。每次只输入一个简短的中文关键词，例如“电力电子技术”，不要输入整句话。"
    "局限：工具只能返回词条相关的百科知识。工具不能搜索实时信息，不能提供关键词相关的新闻热点和实时信息。"),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词，越短越好，比如「电力电子」"},
        },
        "required": ["query"],
    },
}

ALL_TOOLS = [get_time_tool, write_note_tool, search_wikipedia_tool]


# ---------------- 分发：模型点名要哪个工具，就调用哪个函数 ----------------

def run_tool(name, args):
    if name == "get_time":
        return get_time()
    elif name == "write_note":
        return write_note(args["filename"], args["content"])
    elif name == "search_wikipedia":
        return search_wikipedia(args["query"])
    else:
        return "错误：没有叫 " + name + " 的工具。可用的工具有 get_time、write_note、search_wikipedia。"


# ---------------- agent loop ----------------

history = []

while True:
    question = input("\n你：")
    if question == "退出":
        break
    history.append({"role": "user", "content": question})

    step_count = 0
    finished = False

    while step_count < MAX_STEPS:
        step_count = step_count + 1
        print("\n===== 第", step_count, "轮 =====")

        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system="你是一个会使用工具的助手。回答用纯文本，不要用 Markdown 符号。",
            tools=ALL_TOOLS,
            messages=history,
            thinking={"type": "adaptive", "display": "summarized"},  # 显示思考摘要
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        # 模型的回复原样放回记录（思考块带签名，不能改）
        history.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "thinking" and block.thinking:
                print("【思考】", block.thinking)
            if block.type == "text":
                print("【模型说】", block.text)
            if block.type == "tool_use":
                print("【调用工具】", block.name, block.input)
                result = run_tool(block.name, block.input)
                # [:200] 表示只取前 200 个字打印，免得刷屏（交给模型的还是完整结果）
                print("【工具结果】", str(result)[:200])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,     # 必须和 tool_use 的 id 对上
                    "content": str(result),
                })

        # stop_reason == "tool_use"：模型还要用工具，把结果发回去继续
        # 否则就是说完了
        if response.stop_reason == "tool_use":
            history.append({"role": "user", "content": tool_results})
        else:
            finished = True
            break

    if not finished:
        print("⚠️ 已经跑了", MAX_STEPS, "轮还没结束，强制停止")