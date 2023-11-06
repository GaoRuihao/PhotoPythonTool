from PIL import Image, ImageDraw, ImageFont, ImageFilter
# from pillow_heif import register_heif_opener
from geopy.geocoders import Nominatim
import exifread
import os
import shutil
import json
import re
import requests


def latitude_and_longitude_convert_to_decimal_system(*arg):
    try:
        return float(arg[0]) + ((float(arg[1]) + (float(arg[2].split('/')[0]) / float(arg[2].split('/')[-1]) / 60)) / 60)
    except ZeroDivisionError:
        print("除以零错误。")
        return None


def find_GPS_image(pic_path):
    GPS = {}
    date = ''
    with open(pic_path, 'rb') as f:
        tags = exifread.process_file(f)
        for tag, value in tags.items():
            if re.match('GPS GPSLatitudeRef', tag):
                GPS['GPSLatitudeRef'] = str(value)
            elif re.match('GPS GPSLongitudeRef', tag):
                GPS['GPSLongitudeRef'] = str(value)
            elif re.match('GPS GPSAltitudeRef', tag):
                GPS['GPSAltitudeRef'] = str(value)
            elif re.match('GPS GPSLatitude', tag):
                try:
                    match_result = re.match('\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
                    GPS['GPSLatitude'] = int(match_result[0]), int(match_result[1]), int(match_result[2])
                except:
                    deg, min, sec = [x.replace(' ', '') for x in str(value)[1:-1].split(',')]
                    GPS['GPSLatitude'] = latitude_and_longitude_convert_to_decimal_system(deg, min, sec)
            elif re.match('GPS GPSLongitude', tag):
                try:
                    match_result = re.match('\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
                    GPS['GPSLongitude'] = int(match_result[0]), int(match_result[1]), int(match_result[2])
                except:
                    deg, min, sec = [x.replace(' ', '') for x in str(value)[1:-1].split(',')]
                    GPS['GPSLongitude'] = latitude_and_longitude_convert_to_decimal_system(deg, min, sec)
            elif re.match('GPS GPSAltitude', tag):
                GPS['GPSAltitude'] = str(value)
            elif re.match('.*Date.*', tag):
                date = str(value)
    return {'GPS_information': GPS, 'date_information': date}

def findHEIC_address_from_GPS(lat, lng):
    secret_key = 'vtAG8bhmaCAyjdYIc1uoQKf64juqA018'
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

# 定义一个换算函数，功能：将输入的度（时）分秒，经过换算，返回度（时）。例如输入[30, 12, 1761/100]，返回30.204891666666665
def Conversion(data):
    temp_data = [ele.strip() for ele in (str(data).replace('[', '').replace(']', '').split(','))]
    new_data = eval(temp_data[-1]) / 3600 + int(temp_data[1]) / 60 + int(temp_data[0])
    return new_data

def find_address_from_GPS(GPS):
    #使用Geocoding API把经纬度坐标转换为结构化地址。
    if not GPS['GPS_information']:
        print(f"该照片无GPS信息  {GPS}")
        return {"city": "未知GPS"}
    elif GPS['GPS_information']['GPSLatitude'] and GPS['GPS_information']['GPSLongitude']:
        lat, lng = GPS['GPS_information']['GPSLatitude'], GPS['GPS_information']['GPSLongitude']
        print(f"经纬度 信息  {lat},  {lng}")
        return findHEIC_address_from_GPS(lat=lat, lng=lng)
    return {"city": "未知GPS"}
    

# ANSI颜色码
class bcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

# 指定照片和视频所在的文件夹路径
folder_path = "/Users/hao/Desktop/originals"
output_folder_path = "/Users/hao/Desktop/mobile"

# 检查并创建输出文件夹
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

os.chmod(output_folder_path, 0o777)

# 初始化地理编码器
geolocator = Nominatim(user_agent="geoapiExercises")

# 遍历文件夹中的所有文件
for root, dirs, files in os.walk(folder_path):
    for file_name in files:
        if file_name.endswith('.jpg') or file_name.endswith('.jpeg') or file_name.endswith('.png') or file_name.endswith('.heic'):
            file_path = os.path.join(root, file_name)
            try:
                if file_name.endswith('.heic'):
                    # 读取EXIF信息
                    exif_dict = exifread.process_file(open(file_path, 'rb'))
                    # print(f"exif info : {exif_dict}")

                    # print(time_stamp) # 打印新格式的时间戳
                    latitude = Conversion(data=exif_dict['GPS GPSLatitude'])  # 从图片提取纬度并将单位度分秒换算成度
                    # print(latitude)  # 打印纬度
                    longitude = Conversion(data=exif_dict['GPS GPSLongitude'])  # 从图片提取经度并将单位度分秒换算成度

                    address = findHEIC_address_from_GPS(lat=latitude, lng=longitude)
                    if address["city"]:
                            city = address["city"]
                            city_folder_path = os.path.join(output_folder_path, city)
                            # 检查并创建城市文件夹
                            if not os.path.exists(city_folder_path):
                                os.makedirs(city_folder_path)

                            # 设置文件夹权限
                            os.chmod(city_folder_path, 0o777)
                            # 移动照片到对应城市文件夹下
                            shutil.move(file_path, os.path.join(city_folder_path, file_name))
                            print(f"{bcolors.OKGREEN}Moved {file_name} successfully.{bcolors.ENDC}")

                            # 查找对应的视频文件
                            for video_format in [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"]:
                                video_file_name = os.path.splitext(file_name)[0] + "_3" + video_format
                                video_file_path = os.path.join(root, video_file_name)
                                if os.path.exists(video_file_path):
                                    shutil.move(video_file_path, os.path.join(city_folder_path, video_file_name))
                                    print(f"{bcolors.OKGREEN}Moved {video_file_name} successfully.{bcolors.ENDC}")
                else:
                    GPS_info = find_GPS_image(pic_path=file_path)
                    address = find_address_from_GPS(GPS=GPS_info)
                    if address["city"]:
                        city = address['city']
                        city_folder_path = os.path.join(output_folder_path, city)

                        # 检查并创建城市文件夹
                        if not os.path.exists(city_folder_path):
                            os.makedirs(city_folder_path)
                        os.chmod(city_folder_path, 0o777)

                        # 移动照片到对应城市文件夹下
                        shutil.move(file_path, os.path.join(city_folder_path, file_name))
                        print(f"{bcolors.OKGREEN}Moved {file_name} successfully.{bcolors.ENDC}")

                        # 查找对应的视频文件
                        for video_format in [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"]:
                            video_file_name = os.path.splitext(file_name)[0] + "_3" + video_format
                            video_file_path = os.path.join(root, video_file_name)
                            if os.path.exists(video_file_path):
                                shutil.move(video_file_path, os.path.join(city_folder_path, video_file_name))
                                print(f"{bcolors.OKGREEN}Moved {video_file_name} successfully.{bcolors.ENDC}")
                    else:
                        print(f"{bcolors.WARNING} 读取不到exif信息{file_name} from {file_path} {bcolors.ENDC}")
            except (IOError, KeyError, OSError, AttributeError, ValueError) as e:
                # 处理图像读取错误或缺少位置信息等问题
                print(f"{bcolors.FAIL}Error while processing {file_name} from {file_path}: {e}{bcolors.ENDC}")

print("文件整理完成")
