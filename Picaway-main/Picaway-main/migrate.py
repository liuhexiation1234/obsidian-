# migrate.py - 修复版本
import os
import re
import requests
import json
import time
from logger import getLogger
from MatchInfo import MatchInfo
import yaml

logger = getLogger()

# 读取配置文件
with open("config.yml", "r", encoding="utf-8") as yaml_file:
    config = yaml.safe_load(yaml_file)

picgo_server_url = config["migrate"]["picgo"]["server_url"]
result_filepath = config["scan"]["match"]["result_filepath"]


def upload_single_image(image_path):
    """上传单张图片（使用本地文件路径）"""
    if not os.path.exists(image_path):
        logger.error(f"文件不存在: {image_path}")
        return None

    try:
        # 使用本地文件路径（不要转换为file://格式，直接使用路径）
        data = {"list": [image_path]}

        logger.debug(f"上传图片: {os.path.basename(image_path)}")
        response = requests.post(picgo_server_url, json=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                new_url = result["result"][0]
                logger.info(f"  上传成功: {new_url}")
                return new_url
            else:
                logger.error(f"  上传失败: {result.get('message')}")
                return None
        else:
            logger.error(f"  HTTP错误: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"  上传异常: {e}")
        return None


def upload_by_picgo(match):
    """上传匹配中的所有图片"""
    name = match.filepath
    logger.info(f"{name}: 开始上传 {len(match.picUrls)} 张图片")

    new_urls = []
    failed_count = 0

    for i, image_path in enumerate(match.picUrls, 1):
        # 检查文件是否存在
        if not os.path.exists(image_path):
            logger.warning(f"  图片不存在，跳过: {image_path}")
            new_urls.append(None)
            failed_count += 1
            continue

        logger.info(f"  上传第 {i}/{len(match.picUrls)} 张: {os.path.basename(image_path)}")

        new_url = upload_single_image(image_path)
        if new_url:
            new_urls.append(new_url)
        else:
            logger.warning(f"  上传失败，保留原格式")
            new_urls.append(None)
            failed_count += 1

        # 添加延迟，避免请求过快（每张图片间隔1秒）
        if i < len(match.picUrls):
            time.sleep(1)

    if failed_count == len(match.picUrls):
        logger.error(f"{name}: 所有图片上传失败")
        return False

    logger.info(f"{name}: 上传完成，成功 {len(match.picUrls) - failed_count}/{len(match.picUrls)} 张")
    return new_urls


def process_markdown_file(filepath, pic_urls, new_urls):
    """处理单个Markdown文件，替换图片链接"""
    # 读取文件内容
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return False

    # 匹配Obsidian格式的图片
    # 注意：正则表达式要匹配整个![[...]]格式
    obsidian_pic_regex = re.compile(r'(!\[\[(.*?\.(?:png|jpg|jpeg|gif|bmp|svg|webp))(?:\|.*?)?\]\])')
    original_matches = obsidian_pic_regex.findall(content)

    if not original_matches:
        logger.warning(f"文件中未找到图片链接")
        return True

    logger.info(f"  找到 {len(original_matches)} 个图片链接需要替换")

    new_content = content
    replace_count = 0

    # 逐个替换
    for (original_text, image_name), new_url in zip(original_matches, new_urls):
        if new_url is None:
            logger.warning(f"    跳过: {image_name} (上传失败)")
            continue

        # 创建新的Markdown格式
        # 使用文件名（不含扩展名）作为alt文本
        alt_text = os.path.splitext(image_name)[0]
        new_markdown = f"![{alt_text}]({new_url})"

        # 替换
        new_content = new_content.replace(original_text, new_markdown)
        replace_count += 1
        logger.info(f"    替换: {image_name} → {new_url}")

    # 写回文件
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        logger.info(f"  文件保存完成，替换了 {replace_count}/{len(original_matches)} 个图片链接")
        return True
    except Exception as e:
        logger.error(f"  保存文件失败: {e}")
        return False


def main():
    """主函数"""
    # 检查结果文件是否存在
    if not os.path.exists(result_filepath):
        logger.error(f"结果文件不存在: {result_filepath}")
        logger.error("请先运行 scan.py 生成扫描结果")
        return

    # 读取扫描结果
    logger.info("读取扫描结果...")
    try:
        with open(result_filepath, "r", encoding="utf-8") as f:
            matches_data = json.load(f)
    except Exception as e:
        logger.error(f"读取结果文件失败: {e}")
        return

    if not matches_data:
        logger.info("没有需要处理的文件")
        return

    matches = [MatchInfo.from_dict(data) for data in matches_data]
    logger.info(f"开始执行，共 {len(matches)} 个文件需要处理，可能会耗费较长时间，请勿关闭程序!!")

    # 处理每个文件
    processed_count = 0
    failed_count = 0

    for i, match in enumerate(matches, 1):
        logger.info(f"\n[{i}/{len(matches)}] 处理文件: {match.filepath}")

        # 上传图片
        new_urls = upload_by_picgo(match)

        if new_urls is False:
            logger.error(f"  图片上传失败，跳过此文件")
            failed_count += 1
            continue

        # 替换Markdown文件中的链接
        success = process_markdown_file(match.filepath, match.picUrls, new_urls)

        if success:
            processed_count += 1
        else:
            failed_count += 1

        # 文件间延迟
        if i < len(matches):
            logger.info("等待3秒后处理下一个文件...")
            time.sleep(3)

    # 输出总结
    logger.info(f"\n{'=' * 60}")
    logger.info(f"处理完成!")
    logger.info(f"成功处理: {processed_count} 个文件")
    if failed_count > 0:
        logger.info(f"失败: {failed_count} 个文件")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
