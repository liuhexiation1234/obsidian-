# test_local_file_upload.py
import requests
import json


def test_local_file_upload():
    """测试本地文件上传"""
    url = "http://127.0.0.1:36677/upload"

    # 使用一个本地文件路径
    # 注意：PicGo可能需要绝对路径
    test_file = r"C:\Users\16342\Documents\Obsidian Vault\游戏\坚守阵地\附件\Pasted image 20251012194836.png"

    # 测试不同格式的路径
    test_paths = [
        test_file,  # 原始路径
        f"file://{test_file}",  # file:// 协议
        test_file.replace("\\", "/"),  # 正斜杠
        test_file.replace("\\", "\\\\"),  # 双反斜杠
    ]

    for path_format in test_paths:
        print(f"\n测试路径格式: {path_format}")
        data = {"list": [path_format]}

        try:
            response = requests.post(url, json=data, timeout=30)
            result = response.json()

            print(f"  状态码: {response.status_code}")
            print(f"  成功: {result.get('success')}")
            print(f"  消息: {result.get('message')}")

            if result.get("success"):
                print(f"  返回URL: {result.get('result', [])}")
                return True

        except Exception as e:
            print(f"  请求失败: {e}")

    return False


if __name__ == "__main__":
    if test_local_file_upload():
        print("\n✅ 本地文件上传成功！")
    else:
        print("\n❌ 本地文件上传失败")
        print("可能的原因:")
        print("1. PicGo不支持直接上传本地文件路径")
        print("2. 需要安装额外的插件")
        print("3. 路径格式不正确")