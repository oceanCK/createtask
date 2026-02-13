"""
测试飞书图片下载功能
"""
import json
from image_handler import ImageHandler, FeishuImageHelper
from config import get_config

def test_feishu_image():
    config = get_config()
    
    # 先不带token测试
    print("="*60)
    print("测试1: 不带token直接下载飞书CDN图片")
    print("="*60)
    
    handler_no_token = ImageHandler()
    
    # 示例飞书CDN图片URL
    test_urls = [
        "https://s1-imfile.feishucdn.com/static-resource/v1/v3_00rh_f1e2984d-1cd8-41a8-82f0-a2397ee663cg~?image_size=72x72&cut_type=default-face&quality=&format=jpeg&sticker_format=.webp",
    ]
    
    for url in test_urls:
        result = handler_no_token.test_image_download(url)
        print(f"\n无Token测试结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 带token测试
    print("\n" + "="*60)
    print("测试2: 使用飞书token下载")
    print("="*60)
    
    feishu_helper = FeishuImageHelper(
        app_id=config.feishu.app_id,
        app_secret=config.feishu.app_secret
    )
    
    token = feishu_helper.get_access_token()
    print(f"获取到token: {token[:20] if token else 'None'}...")
    
    handler_with_token = feishu_helper.get_image_handler()
    
    for url in test_urls:
        result = handler_with_token.test_image_download(url)
        print(f"\n带Token测试结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_feishu_image()
