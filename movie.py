import os
import subprocess
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import requests
import json
import shutil


# ANSI颜色码
class bcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

def findHEIC_address_from_GPS(lat, lng):
    secret_key = 'uGsotSPrAapKFokoaDoUGIZ27dDA1Ura'
    baidu_map_api = "https://api.map.baidu.com/reverse_geocoding/v3/?ak={0}&output=json&coordtype=wgs84ll&location={1},{2}".format(
        secret_key, lat, lng)
    response = requests.get(baidu_map_api).json()
    status = response['status']

    formatted_addreses = response["result"]["formatted_address"]
    province = response["result"]["addressComponent"]["province"]
    city = response["result"]["addressComponent"]["city"]
    district = response["result"]["addressComponent"]["district"]
    print(f"district info : {district}")
    # return formatted_address, province, city, district
    return {"city": city}

# 从.mov文件中获取经纬度信息
def get_gps_info(file_path):
    command = f'exiftool -c "%.6f" -GPSLatitude -GPSLongitude "{file_path}"'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        output = result.stdout
        print(f"获取到经纬度信息:  {output}")
        return output
    else:
        print(f"无法获取 {file_path} 的经纬度信息。")
        return None

def extract_gps_from_mov(directory):
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(".mov"):
                file_path = os.path.join(root, file_name)
                
                # 获取经纬度信息
                gps_info = get_gps_info(file_path)
                if gps_info:
                    # 解析经纬度信息
                    latitude = None
                    longitude = None
                    for line in gps_info.split('\n'):
                        if 'GPS Latitude' in line:
                            latitude = line.split(':')[-1].strip()
                        elif 'GPS Longitude' in line:
                            longitude = line.split(':')[-1].strip()

                    if latitude and longitude:
                        address = findHEIC_address_from_GPS(lat=latitude, lng=longitude)
                        if address["city"]:
                            city = address["city"]
                            city_folder_path = os.path.join(output_folder_path, city)
                            # 检查并创建城市文件夹
                            if not os.path.exists(city_folder_path):
                                os.makedirs(city_folder_path)

                            # 移动照片到对应城市文件夹下
                            shutil.move(file_path, os.path.join(city_folder_path, file_name))
                            print(f"{bcolors.OKGREEN}Moved {file_name} successfully.{bcolors.ENDC}")

# 指定包含MOV视频的文件夹路径
folder_path = "/Users/hao/Desktop/test"
output_folder_path = "/Users/hao/Desktop/mobile"

# 提取文件夹及其子文件夹中所有MOV视频的经纬度信息
extract_gps_from_mov(folder_path)
