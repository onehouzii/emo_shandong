import requests
from flask import Flask, request

app = Flask(__name__)

# 配置参数
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:5000/callback"  # 本地测试回调地址

# Step 1: 生成授权链接
def generate_auth_url():
    auth_url = f"https://api.weibo.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
    return auth_url

# Step 2: 用户授权后回调处理
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        access_token = get_access_token(code)
        return f"Access Token获取成功: {access_token}"
    else:
        return "授权失败"

# Step 3: 用code换取Access Token
def get_access_token(code):
    token_url = "https://api.weibo.com/oauth2/access_token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(token_url, headers=headers, data=data)
    return response.json().get("access_token")

if __name__ == "__main__":
    print(f"请访问以下链接授权: {generate_auth_url()}")
    app.run(port=5000)