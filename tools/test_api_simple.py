#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 xAI API 连接
"""

import json
import sys
from urllib import request as urlreq
from urllib import error as urlerr

def test_api(api_key: str):
    """测试 API 连接"""
    
    print("测试 xAI API 连接...")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # 简单的测试请求
    payload = {
        "model": "grok-4-fast-reasoning",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' in Chinese."}
        ],
        "temperature": 0.3,
        "max_tokens": 50
    }
    
    try:
        req = urlreq.Request(
            "https://api.x.ai/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
        )
        
        print("发送请求...")
        with urlreq.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        print("✅ API 连接成功！")
        print(f"模型: {result.get('model', 'N/A')}")
        print(f"回复: {result['choices'][0]['message']['content']}")
        print(f"Token 使用: {result.get('usage', {})}")
        return True
        
    except urlerr.HTTPError as e:
        print(f"❌ HTTP 错误 {e.code}")
        try:
            error_body = e.read().decode('utf-8')
            error_json = json.loads(error_body)
            print(f"错误详情: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"错误内容: {e.read().decode('utf-8', errors='ignore')}")
        return False
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python test_api_simple.py YOUR_API_KEY")
        sys.exit(1)
    
    api_key = sys.argv[1]
    success = test_api(api_key)
    sys.exit(0 if success else 1)
