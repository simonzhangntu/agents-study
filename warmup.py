# 1. 列表：一个装东西的盒子
fruits = []
fruits.append("苹果")   # 往盒子里放一个
fruits.append("香蕉")
print(fruits)           # ['苹果', '香蕉']
print(len(fruits))      # 盒子里有几个：2

# 2. input + while 循环 + break
while True:                     # 一直重复下面缩进的代码
    word = input("说点什么：")   # 停下来等你打字，回车后存进 word
    if word == "退出":
        break                   # 跳出循环
    print("你说的是：", word)
print("结束了")