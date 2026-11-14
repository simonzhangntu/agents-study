from datetime import datetime
import anthropic
import requests
import json
import os

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
MAX_STEPS = 6
MEMORY_FILE = "memory.json"
NOTES_DIR = "my_notes"


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


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_memory(fact):
    facts = load_memory()
    if fact in facts:
        return "这条已经记住了，不需要重复保存：" + fact
    facts.append(fact)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)
    return "已记住：" + fact

def search_notes(query):
    if not os.path.exists(NOTES_DIR):
        return "错误：找不到笔记文件夹" + NOTES_DIR + "。请告诉用户先创建它并放入笔记。"

    keywords = query.split()
    scored = []

    for filename in os.listdir(NOTES_DIR):
        path = os.path.join(NOTES_DIR, filename)   # 拼出完整路径，比如 my_notes/01_充电器.md
        with open(path, encoding="utf-8") as f:
            text = f.read()

        score = 0
        for word in keywords:
            score = score + text.count(word)

        if score > 0:   # 至少命中一次才算相关
            scored.append([score, filename, text])

    if len(scored) == 0:
        return "没有找到和「" + query + "」相关的笔记。可以换几个更短、更常见的关键词再试，关键词之间用空格隔开。"

    scored.sort(reverse=True)   # 按分数从高到低排序

    result = ""
    for item in scored[:3]:     # 只取前 3 篇
        result = result + "【" + item[1] + "】（相关度 " + str(item[0]) + "）\n" + item[2] + "\n"
    return result


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

save_memory_tool = {
    "name":"save_memory",
    "description":"把一条关于用户的事实长期保存，下次启动时候还可以记得。"
    "只有和用户的个人信息相关时才进行保存，例如用户的姓名、职业、喜好、账号定位、喜欢的风格等。"
    "什么时候不用：和用户本人无关的信息、临时性的信息、用户的任何密码、涉及个人敏感信息不保存。"
    "记忆fact遵循什么格式：一句完整的话。用“用户……”开头，例如“用户的小红书定位是电力电子知识科普。”",
    "input_schema":{
        "type":"object",
        "properties":{
            "fact":{"type":"string","description":"要记住的一条事实，一句完整的话"},
        },
        "required":["fact"],
    },
}

search_notes_tool = {
    "name": "search_notes",
    "description": (
        "在用户自己的小红书笔记库里按关键词搜索，返回最相关的最多 3 篇笔记，包括标题、点赞收藏数据和内容摘要。"
        "需要参考用户过往写过什么、哪类内容数据好、避免选题重复时使用。"
        "关键词要短，多个关键词之间用空格隔开，比如「PWM 占空比」。"
        "局限：只按关键词字面匹配，意思相近但用词不同的笔记可能搜不到，这时可以换个说法再搜一次。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词，多个用空格隔开"},
        },
        "required": ["query"],
    },
}

ALL_TOOLS = [get_time_tool, write_note_tool, search_wikipedia_tool, save_memory_tool, search_notes_tool]




# ---------------- 分发：模型点名要哪个工具，就调用哪个函数 ----------------

def run_tool(name, args):
    if name == "get_time":
        return get_time()
    elif name == "write_note":
        return write_note(args["filename"], args["content"])
    elif name == "search_wikipedia":
        return search_wikipedia(args["query"])
    elif name == "save_memory":
        return save_memory(args["fact"])
    elif name == "search_notes":
        return search_notes(args["query"])
    else:
        return "错误：没有叫 " + name + " 的工具。可用的工具有 get_time、write_note、search_wikipedia、save_memory、search_notes。"


# ---------------- agent loop ----------------

facts = load_memory()
memory_text = ""
for fact in facts:
    memory_text = memory_text + "-" +fact +"\n"
if memory_text == "":
    memory_text = "(暂时还没有)\n"
print("【启动时读到的记忆】\n" + memory_text)

SYSTEM = ("你是一个会使用工具的助手。回答用纯文本，不要用 Markdown 符号。\n"
    "下面是你记住的关于用户的长期信息，回答时要参考：\n"
    + memory_text
    + "当用户透露关于自己的、以后也有用的信息时，用save_memory工具记录下来。")

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
            system=SYSTEM,
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