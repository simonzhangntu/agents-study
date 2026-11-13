一个用Gemini/Claude从零写的命令行agent
这个agent loop是通过用户输入，模型，工具，模型，答案的模式运行的，直到用户手动输出“退出”才会停止。
有四个工具：calculator，get_time，read_file，write_note。
需要安装gemini的python库，设置api key，python assistant.py