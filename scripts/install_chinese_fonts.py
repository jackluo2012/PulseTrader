#!/usr/bin/env python3
"""
中文字体安装和检测脚本
"""
import subprocess
import os
from pathlib import Path

def check_font_installed(font_name):
    """检查字体是否已安装"""
    try:
        result = subprocess.run(['fc-list', ':', 'family'], 
                              capture_output=True, text=True)
        return font_name.lower() in result.stdout.lower()
    except Exception:
        return False

def install_chinese_fonts():
    """安装中文字体"""
    required_packages = [
        'fonts-wqy-microhei',
        'fonts-wqy-zenhei',
        'fonts-noto-cjk'
    ]
    
    print("检查并安装中文字体...")
    
    try:
        # 更新包列表
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        
        # 安装字体包
        for package in required_packages:
            if not check_font_installed(package.split('-')[-1]):
                print(f"安装 {package}...")
                subprocess.run(['sudo', 'apt', 'install', '-y', package], check=True)
            else:
                print(f"{package} 已安装")
        
        # 清除字体缓存
        subprocess.run(['fc-cache', '-fv'], check=True)
        
        print("\n✅ 字体安装完成")
        print("已安装以下字体包：")
        for package in required_packages:
            print(f"  - {package}")
            
    except Exception as e:
        print(f"❌ 安装过程中出错: {e}")
        print("请手动运行以下命令：")
        print("sudo apt update")
        print("sudo apt install -y " + " ".join(required_packages))
        print("fc-cache -fv")

if __name__ == "__main__":
    install_chinese_fonts()