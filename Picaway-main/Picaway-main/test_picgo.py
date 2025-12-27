# test_picgo_setup.py
import requests
import json


def test_picgo_upload_single_image():
    """测试上传单张网络图片"""
    url = "http://127.0.0.1:36677/upload"

    # 使用一个小的测试图片URL
    test_image_url = "https://raw.githubusercontent.com/mui/material-ui/master/docs/public/static/logo.png"

    print("测试1: 上传网络图片")
    print(f"使用图片: {test_image_url}")

    try:
        response = requests.post(url, json={"list": [test_image_url]}, timeout=30)
        result = response.json()

        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, indent=2)}")

        if result.get("success"):
            print("✅ 网络图片上传成功!")
            return True
        else:
            print(f"❌ 网络图片上传失败: {result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_picgo_config():
    """测试PicGo当前配置"""
    url = "http://127.0.0.1:36677/"

    print("测试PicGo服务状态...")
    try:
        response = requests.get(url, timeout=5)
        print(f"PicGo服务状态: {response.status_code}")
        return True
    except:
        print("PicGo服务未启动!")
        return False


def check_picgo_current_uploader():
    """检查当前使用的上传器"""
    print("\n当前PicGo配置分析:")
    print("1. 从日志看，当前上传器是: [tcyun] (腾讯云COS)")
    print("2. 常见问题:")
    print("   - SecretId/SecretKey 错误或过期")
    print("   - Bucket 不存在或无权访问")
    print("   - Region 配置错误")
    print("   - 存储路径(CustomUrl)配置错误")


if __name__ == "__main__":
    print("=" * 60)
    print("PicGo 配置测试")
    print("=" * 60)

    # 测试服务状态
    if not test_picgo_config():
        print("请先启动PicGo并开启Server服务")
        exit(1)

    # 测试上传
    if not test_picgo_upload_single_image():
        check_picgo_current_uploader()
        print("\n建议:")
        print("1. 在PicGo界面手动上传一张图片测试")
        print("2. 检查腾讯云COS配置")
        print("3. 尝试更换图床（如GitHub图床）")