"""
虚拟环境字体配置模块
解决matplotlib在虚拟环境中的中文字体显示问题
"""
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path


class VirtualEnvFontManager:
    """虚拟环境字体管理器"""

    def __init__(self):
        self.font_cache_dir = Path.home() / ".matplotlib" / "fontlist-v330.json"
        self.virtual_env_path = Path(sys.prefix)
        self.setup_complete = False

    def find_system_fonts(self):
        """查找系统中所有可用的字体文件"""
        font_paths = []

        # 常见系统字体目录
        system_font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "/snap/fonts/common/fonts",
            str(Path.home() / ".fonts"),
            str(Path.home() / ".local" / "share" / "fonts"),
        ]

        for font_dir in system_font_dirs:
            if os.path.exists(font_dir):
                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        if file.lower().endswith(('.ttf', '.ttc', '.otf')):
                            font_paths.append(os.path.join(root, file))

        return font_paths

    def detect_chinese_fonts(self):
        """检测中文字体"""
        font_paths = self.find_system_fonts()
        chinese_fonts = []

        chinese_font_names = [
            "droid", "wqy", "noto", "cjk", "source han", "arphic",
            "uming", "ukai", "zenhei", "microhei", "simhei", "microsoft"
        ]

        for font_path in font_paths:
            try:
                # 尝试获取字体名称
                font_prop = fm.FontProperties(fname=font_path)
                font_name = font_prop.get_name().lower()

                # 检查是否包含中文字体特征
                if any(cn in font_name for cn in chinese_font_names):
                    chinese_fonts.append({
                        'path': font_path,
                        'name': font_prop.get_name(),
                        'family': font_prop.get_family()
                    })
            except Exception:
                continue

        return chinese_fonts

    def setup_matplotlib_fonts(self):
        """配置matplotlib字体"""
        if self.setup_complete:
            return True

        # 检测中文字体
        chinese_fonts = self.detect_chinese_fonts()

        # 构建字体列表
        font_list = [
            'DejaVu Sans',           # 默认英文字体
            'Liberation Sans',       # Linux英文字体
            'Arial',                 # 通用英文字体
        ]

        # 添加检测到的中文字体
        for font_info in chinese_fonts:
            try:
                # 手动添加字体到matplotlib
                fm.fontManager.addfont(font_info['path'])
                font_list.append(font_info['name'])
                print(f"✅ 添加中文字体: {font_info['name']}")
            except Exception as e:
                print(f"⚠️ 无法添加字体 {font_info.get('name', font_info.get('path'))}: {e}")

        # 添加常见中文字体名称（作为备选）
        font_list.extend([
            'WenQuanYi Micro Hei',
            'WenQuanYi Zen Hei',
            'AR PL UMing CN',
            'AR PL UKai CN',
            'Noto Sans CJK SC',
            'Source Han Sans SC',
            'Droid Sans Fallback',
            'SimHei',
            'Microsoft YaHei',
        ])

        # 应用字体设置
        plt.rcParams['font.sans-serif'] = font_list
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10

        # 清除字体缓存并重建
        try:
            if hasattr(fm.fontManager, 'cache'):
                fm.fontManager.cache.clear()
            if hasattr(fm, '_rebuild'):
                fm._rebuild()
        except Exception:
            pass

        self.setup_complete = True

        if chinese_fonts:
            print(f"✅ 字体配置完成，找到 {len(chinese_fonts)} 个中文字体")
            return True
        else:
            print("⚠️ 未找到中文字体，将使用默认字体")
            return False

    def test_chinese_display(self):
        """测试中文显示"""
        try:
            # 创建简单图表测试
            import matplotlib.pyplot as plt
            import numpy as np

            fig, ax = plt.subplots(figsize=(1, 1))
            ax.text(0.5, 0.5, '中文测试', fontsize=12, ha='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

            # 保存到临时文件
            temp_file = '/tmp/chinese_font_test.png'
            plt.savefig(temp_file, dpi=100, bbox_inches='tight')
            plt.close()

            # 检查文件是否生成
            if os.path.exists(temp_file):
                os.remove(temp_file)
                return True
            else:
                return False

        except Exception as e:
            print(f"字体测试失败: {e}")
            return False


# 全局字体管理器实例
_font_manager = None

def setup_chinese_fonts():
    """设置中文字体支持（虚拟环境专用）"""
    global _font_manager

    if _font_manager is None:
        _font_manager = VirtualEnvFontManager()

    return _font_manager.setup_matplotlib_fonts()

def get_font_manager():
    """获取字体管理器实例"""
    global _font_manager

    if _font_manager is None:
        _font_manager = VirtualEnvFontManager()
        _font_manager.setup_matplotlib_fonts()

    return _font_manager

def auto_setup():
    """自动设置字体（导入时自动调用）"""
    try:
        success = setup_chinese_fonts()

        # 如果字体设置失败，提供解决方案建议
        if not success:
            print("💡 中文字体支持建议：")
            print("   1. 安装系统中文字体包:")
            print("      sudo apt install fonts-wqy-zenhei fonts-wqy-microhei")
            print("   2. 或者使用英文标签避免显示问题")

        return success

    except Exception as e:
        print(f"⚠️ 字体自动设置失败: {e}")
        return False

# 模块导入时自动设置
auto_setup()
