* 飞书多维表自动化的 HTTP 请求是从飞书云端服务器发起的，而不是本地网络发起。
所以飞书无法访问本地的内网 IP 10.20.21.48，会导致403错误

解决方案：

需要将本地服务暴露到公网。推荐使用 ngrok 内网穿透

使用步骤
1. 注册 ngrok 账号（免费）
访问 https://dashboard.ngrok.com/signup 注册账号

2. 获取 Authtoken
登录后在 https://dashboard.ngrok.com/get-started/your-authtoken 复制你的 token

3. 配置 Authtoken
在终端运行（把 YOUR_TOKEN 替换成你复制的 token）：
E:\KK\飞书一键建单\tools\ngrok.exe config add-authtoken YOUR_TOKEN

4. 启动 ngrok
确保 main.py 服务已在 8080 端口运行，然后：
E:\KK\飞书一键建单\tools\ngrok.exe http 8080

5. 获取公网 URL
启动后会显示类似：
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8080

6. 更新飞书多维表配置
将 webhook URL 改为：
https://abc123.ngrok-free.app/webhook/feishu


