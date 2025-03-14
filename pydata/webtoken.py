import requests
from urllib.parse import quote

# 你的应用信息
CLIENT_ID = '2740570086'
CLIENT_SECRET = '5c9cdc3b9f6bc0f372e47e25d95f7375'
REDIRECT_URI = 'http://127.0.0.1:8080/callback'  # 需要和开放平台设置的一致

# 第一步：获取授权码
auth_url = f'https://api.weibo.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={quote(REDIRECT_URI)}'
print(f"请访问以下URL授权: {auth_url}")

# 用户授权后会跳转到REDIRECT_URI，从回调URL中获取code参数
code = input("请输入回调URL中的code参数: ")

# 第二步：获取Access Token
token_url = 'https://api.weibo.com/oauth2/access_token'
data = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': REDIRECT_URI
}

response = requests.post(token_url, data=data)
access_token = response.json()['access_token']
