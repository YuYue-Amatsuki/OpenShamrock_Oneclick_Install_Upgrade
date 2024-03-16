import subprocess
import requests
import re
import datetime
import zipfile
import io
from tqdm import tqdm
import logging
import os

url = 'https://nightly.link/whitechi73/OpenShamrock/workflows/build-apk/master?preview'
search_term = r'https://nightly\.link/whitechi73/OpenShamrock/workflows/build-apk/master/Shamrock.*arm64\.zip'

# 获取logger实例
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建一个用于输出到控制台的处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 将处理器添加到logger
logger.addHandler(console_handler)

logger.info(f"{datetime.datetime.now()} - 正在下载最新版OpenShamrock")

response = requests.get(url)
html_content = response.text

download_links = re.findall(r'href=[\'"](.*?)[\'"]', html_content)
for link in download_links:
    if re.match(search_term, link):
        file_request = requests.get(link, stream=True)
        file_name = link.split('/')[-1]

        # 获取脚本文件的路径
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # 构建下载文件的保存路径
        file_path = os.path.join(script_dir, file_name)

        # 保存文件并显示下载进度条
        with open(file_path, 'wb') as f:
            total_length = int(file_request.headers.get('content-length'))
            for chunk in tqdm(file_request.iter_content(chunk_size=8192), total=total_length/8192, unit='KB'):
                if chunk:
                    f.write(chunk)

        logger.info(f"{file_name} 已下载")

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

        # 列出连接到计算机上的所有安卓设备的序号和设备信息
        adb_devices = subprocess.run(['adb', 'devices'], capture_output=True, text=True).stdout
        # 检查是否存在连接的设备
        if "List of devices attached" not in adb_devices:
            logger.info("未检测到已连接的设备，请连接设备后重新运行程序。")
        else:
            devices_list = adb_devices.split('\n')[1:-2]  # 去除开头和结尾多余信息

        # 打印设备列表供用户选择
        for idx, device in enumerate(devices_list):
            print(f"设备序号: {idx+1}, 设备名称: {device}")

        # 用户选择要安装文件的设备
        selected_device_idx = int(input("请选择要安装OpenShamrock的设备序号: "))
        selected_device = devices_list[selected_device_idx - 1].split('\t')[0]

        # 使用 adb 安装解压后的文件到所选设备
        apk_file_path = os.path.join(script_dir, extracted_file_path)
        subprocess.run(['adb', '-s', selected_device, 'install', apk_file_path])

        # 删除安装包
        os.remove(apk_file_path)