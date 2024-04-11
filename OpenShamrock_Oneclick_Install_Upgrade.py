import subprocess
import requests
import re
import datetime
import zipfile
import io
from tqdm import tqdm
import logging
import os
import time

# 获取logger实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建一个用于输出到控制台的处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 将处理器添加到logger
logger.addHandler(console_handler)

logger.info(f"{datetime.datetime.now()} - 正在下载最新版OpenShamrock")


url_latest = 'https://nightly.link/whitechi73/OpenShamrock/workflows/build-apk/master?preview'
url_1_0_9 = 'https://nightly.link/whitechi73/OpenShamrock/workflows/build-apk/v1.0.9?preview'

versions = {
    '1.1.0 (Kritor)': url_latest,
    '1.0.9 (OneBot)': url_1_0_9
}

selected_version = None

while selected_version is None:
    print("请选择要下载的版本：")
    for idx, version in enumerate(versions.keys()):
        print(f"{idx+1}. {version}")

    user_input = input("请输入版本序号：")

    if user_input.isdigit():
        selected_version_idx = int(user_input)
        if selected_version_idx in range(1, len(versions) + 1):
            selected_version = list(versions.keys())[selected_version_idx - 1]
        else:
            print("无效的选择，请重新输入：")
    else:
        print("无效的选择，请重新输入：")

architectures = {
    'all': r'https://nightly\.link/whitechi73/OpenShamrock/workflows/build-apk/.*/Shamrock.*all\.zip',
    'arm64': r'https://nightly\.link/whitechi73/OpenShamrock/workflows/build-apk/.*/Shamrock.*arm64\.zip',
    'x86_64': r'https://nightly\.link/whitechi73/OpenShamrock/workflows/build-apk/.*/Shamrock.*x86_64\.zip'
}

response = requests.get(versions[selected_version])
html_content = response.text

download_links = re.findall(r'href=[\'"](.*?)[\'"]', html_content)

# 提示用户选择 CPU 架构
selected_architecture = None

while selected_architecture is None:
    print("请选择对应的CPU架构：")
    for idx, architecture in enumerate(architectures.keys()):
        print(f"{idx+1}. {architecture}")

    user_input = input("请输入序号：")
    
    if user_input.isdigit():
        selected_architecture_idx = int(user_input)
        if selected_architecture_idx in range(1, len(architectures) + 1):
            selected_architecture = list(architectures.keys())[selected_architecture_idx - 1]
        else:
            print("无效的选择，请重新输入：")
    else:
        print("无效的选择，请重新输入：")

# 根据选择的 CPU 架构获取对应的下载链接
selected_download_link = None
for link in download_links:
    if re.match(architectures[selected_architecture], link):
        selected_download_link = link
        break

file_request = requests.get(selected_download_link, stream=True)
file_name = selected_download_link.split('/')[-1]

# 获取脚本文件的路径
script_dir = os.path.dirname(os.path.realpath(__file__))

# 构建下载文件的保存路径
file_path = os.path.join(script_dir, file_name)

# 保存文件并显示下载进度条
with open(file_path, 'wb') as f:
    total_length = int(file_request.headers.get('content-length'))
    for chunk in tqdm(file_request.iter_content(chunk_size=8192), total=round(total_length/8192), unit='KB', bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]', dynamic_ncols=True, desc=file_name):
        if chunk:
            f.write(chunk)

logger.info(f"{datetime.datetime.now()} - {file_name} 已下载")

# 解压下载的ZIP文件
with zipfile.ZipFile(file_path, 'r') as zip_ref:
    # 解压到当前脚本所在的路径
    zip_ref.extractall(script_dir)
    extracted_files = zip_ref.namelist()  # 获取解压后的文件列表

    # 打印解压后的文件路径
    for extracted_file in extracted_files:
        extracted_file_path = os.path.join(script_dir, extracted_file)

# 删除原始的ZIP文件
os.remove(file_path)

selected_device = None

while selected_device is None:
    adb_devices = subprocess.run(['adb', 'devices'], capture_output=True, text=True).stdout

    if "List of devices attached" not in adb_devices:
        print(f"{datetime.datetime.now()} - 未检测到已连接的设备，请连接设备后重新运行程序。")
        print("程序将在5秒后退出")
        time.sleep(5)
        exit()

    devices_list = adb_devices.split('\n')[1:-2]  # 去除开头和结尾多余信息
    
    if not devices_list:
        print(f"{datetime.datetime.now()} - 未检测到已连接的设备，请连接设备后重新运行程序。")
        print("程序将在5秒后退出")
        time.sleep(5)
        exit()

    for idx, device in enumerate(devices_list):
        print(f"设备序号: {idx + 1}, 设备名称: {device}")

    user_input = input("请选择要安装OpenShamrock的设备序号: ")
    
    if user_input.isdigit():
        selected_device_idx = int(user_input)
        if selected_device_idx in range(1, len(devices_list) + 1):
            selected_device = devices_list[selected_device_idx - 1].split('\t')[0]
        else:
            print("无效的选择，请重新输入：")
    else:
        print("无效的选择，请重新输入：")

# 使用 adb 安装解压后的文件到所选设备
apk_file_path = os.path.join(script_dir, extracted_file_path)
subprocess.run(['adb', '-s', selected_device, 'install', '-r', apk_file_path])
print(f"{datetime.datetime.now()} - 安装完成")

# 删除安装包
os.remove(apk_file_path)
print("程序将在5秒后退出")
time.sleep(5)