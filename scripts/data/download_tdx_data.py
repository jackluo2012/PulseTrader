#!/usr/bin/env python3
"""
通达信数据下载工具
"""

import argparse
import logging
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

import requests

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class TDXDataDownloader:
    """通达信数据下载器"""

    def __init__(self, data_dir: Path = None):
        """
        初始化下载器

        Args:
            data_dir: 数据目录路径
        """
        if data_dir is None:
            self.data_dir = Path("data/tdx")
        else:
            self.data_dir = data_dir

        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 通达信数据下载URL
        self.base_url = "http://localhost:8086/hsjday.zip"

    def download_file(self, url: str, local_path: Path, timeout: int = 300) -> bool:
        """
        下载文件

        Args:
            url: 下载URL
            local_path: 本地保存路径
            timeout: 超时时间（秒）

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"开始下载: {url}")

            # 创建请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # 发送HTTP请求
            response = requests.get(url, headers=headers, stream=True, timeout=timeout)
            response.raise_for_status()

            # 确保目标目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}%", end="", flush=True)

            print()  # 换行

            logger.info(f"下载完成: {local_path}")
            return True

        except Exception as e:
            logger.error(f"下载失败 {url}: {e}")
            return False

    def extract_zip(self, zip_path: Path, extract_dir: Path) -> bool:
        """
        解压ZIP文件

        Args:
            zip_path: ZIP文件路径
            extract_dir: 解压目录

        Returns:
            解压是否成功
        """
        try:
            logger.info(f"开始解压: {zip_path}")

            # 确保解压目录存在
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for file_info in zip_ref.infolist():
                    # 检查路径是否安全，防止路径穿越攻击
                    filename = file_info.filename.replace("\\", "/")  # 统一分隔符
                    if os.path.isabs(filename) or ".." in filename:
                        logger.warning(f"跳过不安全的文件路径: {file_info.filename}")
                        continue

                    full_path = extract_dir / filename

                    # 确保目标路径在解压目录内
                    try:
                        full_path.resolve().relative_to(extract_dir.resolve())
                    except ValueError:
                        logger.warning(f"跳过不安全的文件路径: {file_info.filename}")
                        continue

                    # 始终确保父目录存在
                    full_path.parent.mkdir(parents=True, exist_ok=True)

                    # 如果是目录（以 / 结尾），只创建目录
                    if filename.endswith("/"):
                        full_path.mkdir(parents=True, exist_ok=True)
                        continue

                    # 解压文件，同时保留文件权限
                    with zip_ref.open(file_info) as source:
                        with open(full_path, "wb") as target:
                            target.write(source.read())

                    # 设置文件权限
                    if file_info.external_attr > 0:
                        os.chmod(full_path, file_info.external_attr >> 16)

            logger.info(f"解压完成: {extract_dir}")
            return True

        except Exception as e:
            logger.error(f"解压失败 {zip_path}: {e}")
            return False

    def clear_directory(self, directory: Path) -> bool:
        """
        清空指定目录下的所有文件和子目录

        Args:
            directory: 要清空的目录路径

        Returns:
            清空是否成功
        """
        try:
            if not directory.exists():
                return True

            # 遍历目录中的所有内容
            for item in directory.iterdir():
                if item.is_file():
                    # 如果是文件，直接删除
                    item.unlink()
                elif item.is_dir():
                    # 如果是目录，递归删除其中的所有内容
                    for subitem in item.iterdir():
                        if subitem.is_file():
                            subitem.unlink()
                        else:
                            self.clear_directory(subitem)
                    # 删除空目录
                    item.rmdir()

            logger.info(f"成功清空目录: {directory}")
            return True

        except Exception as e:
            logger.error(f"清空目录失败 {directory}: {e}")
            return False

    def download_all_data(self, force: bool = False) -> bool:
        """
        下载所有通达信数据

        Args:
            force: 是否强制重新下载

        Returns:
            下载是否成功
        """
        success = True

        url = self.base_url
        name = "hsjday"
        # 构造本地路径
        zip_filename = f"{name}.zip"
        zip_path = self.data_dir / zip_filename

        # 检查是否需要下载
        if not force and zip_path.exists():
            logger.info(f"文件已存在，跳过下载: {zip_filename}")
        else:
            # 下载ZIP文件
            if not self.download_file(url, zip_path):
                success = False

            # 解压文件
            extract_dir = self.data_dir / "vipdoc"
            if extract_dir.exists():
                self.clear_directory(extract_dir)
            if not self.extract_zip(zip_path, extract_dir):
                success = False

            # 删除ZIP文件以节省空间
            try:
                zip_path.unlink()
                logger.info(f"删除ZIP文件: {zip_filename}")
            except Exception as e:
                logger.warning(f"删除ZIP文件失败: {e}")

        return success

    def check_data_integrity(self) -> dict:
        """
        检查数据完整性

        Returns:
            完整性检查结果
        """
        result = {
            "vipdoc_sh_exists": False,
            "vipdoc_sz_exists": False,
            "sh_files_count": 0,
            "sz_files_count": 0,
            "total_size_mb": 0,
        }

        try:
            vipdoc_dir = self.data_dir / "vipdoc"

            if vipdoc_dir.exists():
                # 检查沪市数据
                sh_dir = vipdoc_dir / "sh" / "lday"
                if sh_dir.exists():
                    result["vipdoc_sh_exists"] = True
                    for file_path in sh_dir.glob("sh*.day"):
                        result["sh_files_count"] += 1
                        if file_path.is_file():
                            result["total_size_mb"] += file_path.stat().st_size / (
                                1024 * 1024
                            )

                # 检查深市数据
                sz_dir = vipdoc_dir / "sz" / "lday"
                if sz_dir.exists():
                    result["vipdoc_sz_exists"] = True
                    for file_path in sz_dir.glob("sz*.day"):
                        result["sz_files_count"] += 1
                        if file_path.is_file():
                            result["total_size_mb"] += file_path.stat().st_size / (
                                1024 * 1024
                            )

        except Exception as e:
            logger.error(f"检查数据完整性失败: {e}")

        return result


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="通达信数据下载工具")
    parser.add_argument("--data-dir", type=Path, help="数据目录路径")
    parser.add_argument("--force", action="store_true", help="强制重新下载")
    parser.add_argument("--check-only", action="store_true", help="仅检查数据完整性")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 创建下载器
    downloader = TDXDataDownloader(args.data_dir)
    # result = downloader.check_data_integrity()
    # print(result)
    # return
    if args.check_only:
        # 仅检查数据完整性
        print("=== 数据完整性检查 ===")
        result = downloader.check_data_integrity()

        print(f"沪市数据目录: {'存在' if result['vipdoc_sh_exists'] else '不存在'}")
        print(f"深市数据目录: {'存在' if result['vipdoc_sz_exists'] else '不存在'}")
        print(f"沪市文件数量: {result['sh_files_count']}")
        print(f"深市文件数量: {result['sz_files_count']}")
        print(f"总数据大小: {result['total_size_mb']:.2f} MB")

        if result["sh_files_count"] > 0 and result["sz_files_count"] > 0:
            print("\n✅ 数据完整性检查通过")
        else:
            print("\n❌ 数据不完整，建议重新下载")

    else:
        # 下载数据
        print("=== 通达信数据下载 ===")
        print(f"数据目录: {downloader.data_dir}")
        success = downloader.download_all_data(force=args.force)

        if success:
            print("\n✅ 数据下载成功")

            # 检查下载结果
            result = downloader.check_data_integrity()
            print(f"\n下载统计:")
            print(f"  沪市文件: {result['sh_files_count']} 个")
            print(f"  深市文件: {result['sz_files_count']} 个")
            print(f"  总大小: {result['total_size_mb']:.2f} MB")
        else:
            print("\n❌ 数据下载失败")
            sys.exit(1)


if __name__ == "__main__":
    main()
