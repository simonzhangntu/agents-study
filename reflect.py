import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"



def ask(role, text):
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=role,
        messages=[{"role":"user", "content":text}],
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    if response.stop_reason == "refusal":
        return "(模型拒绝了这个要求)"

    answer = ""
    for block in response.content:
        if block.type == "text":
            answer = answer + block.text
    return answer


topic = input("笔记主题：")

draft = ask("你是一个小红书博主", "围绕这个主题写一篇150字以内的小红书笔记，带标题"+topic)
print("=====初稿=====")
print(draft)


critique = ask(
    "你是一个严格的小红书运营编辑。你只负责挑问题，不要改写。",
    "请从下面3个方面给这篇笔记挑毛病，每条一句话：\n"
    "1.标题够不够吸引人\n"
    "2.有没有具体的干货\n"
    "3.读起来像不像广告\n\n"
    "笔记：\n" + draft,)
print("=====自评=====")
print(critique)

final = ask(
    "你是一个小红书博主，你之前已经围绕以" + topic + "为主题写了一个150字以内的笔记",
    "现在你需要依据修改意见对原始笔记进行修改和迭代，最终的笔记也要控制在150字以内\n"
    "意见：\n" + critique + "\n\n"
    "原始笔记：\n" + draft,)

print("=====最终修改的笔记=====")
print(final)
