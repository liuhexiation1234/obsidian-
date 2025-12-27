import os
import re
import json
from logger import getLogger
from MatchInfo import MatchInfo
import yaml

logger = getLogger()

# 读取配置文件
with open("config.yml", "r", encoding="utf-8") as yaml_file:
    config = yaml.safe_load(yaml_file)

directory = config["scan"]["directory"]
md_regex = re.compile(config["scan"]["match"]["md_regex"])
result_filepath = config["scan"]["match"]["result_filepath"]

# 打开输出文件
output_file = open(result_filepath, "w", encoding="utf-8")
matches = []

# Obsidian图片正则表达式
obsidian_pic_regex = re.compile(r'!\[\[(.*?\.(?:png|jpg|jpeg|gif|bmp|svg|webp))(?:\|.*?)?\]\]')


def find_image_file(image_name, md_file_path, vault_root):
    """查找图片文件的完整路径"""
    # 1. 检查与md文件同一目录
    same_dir = os.path.join(os.path.dirname(md_file_path), image_name)
    if os.path.exists(same_dir):
        return same_dir

    # 2. 检查常见的附件文件夹
    common_folders = ['附件', 'assets', 'Attachments', 'images', 'Pictures']

    for folder in common_folders:
        # 在当前目录下的附件文件夹
        test_path = os.path.join(os.path.dirname(md_file_path), folder, image_name)
        if os.path.exists(test_path):
            return test_path

        # 在仓库根目录下的附件文件夹
        test_path = os.path.join(vault_root, folder, image_name)
        if os.path.exists(test_path):
            return test_path

    # 3. 检查仓库根目录本身（新增）
    root_image = os.path.join(vault_root, image_name)
    if os.path.exists(root_image):
        return root_image

    # 4. 如果都没有找到，返回None
    return None


# 遍历目录下的所有文件和子目录
for root, dirs, files in os.walk(directory):
    for filename in files:
        # 如果是Markdown文件，读取内容并匹配图片链接
        if md_regex.match(filename):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 匹配Obsidian格式的图片
                    raw_matches = obsidian_pic_regex.findall(content)

                    if raw_matches:
                        picUrls = []
                        for image_name in raw_matches:
                            # 查找图片文件的完整路径
                            img_path = find_image_file(image_name, filepath, directory)
                            if img_path and os.path.exists(img_path):
                                # 保存完整路径
                                picUrls.append(img_path)
                                logger.info(f"找到图片: {image_name} -> {img_path}")
                            else:
                                logger.warning(f"未找到图片文件: {image_name}")

                        if picUrls:
                            matchInfo = MatchInfo(filepath, picUrls)
                            matches.append(matchInfo)
            except Exception as e:
                logger.error(f"读取文件失败 {filepath}: {e}")

# 序列化对象列表为 JSON
serialized_list = [match.to_dict() for match in matches]
json.dump(serialized_list, output_file, indent=4, ensure_ascii=False)
# 关闭输出文件
output_file.close()

logger.info(f"图片扫描完成，找到 {len(matches)} 个包含图片的文件")
logger.info("请检查是否有不需要迁移的图片, 然后再执行migrate脚本上传")
