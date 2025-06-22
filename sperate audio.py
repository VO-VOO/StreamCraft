import os
import subprocess
import sys
import shutil
import tempfile
import uuid 
import time
import tkinter as tk
from tkinter import filedialog


def is_video_file(file_path):
    """判断文件是否为视频文件"""
    video_extensions = [
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".3gp",
    ]
    _, ext = os.path.splitext(file_path)
    return ext.lower() in video_extensions


def select_folder_with_tkinter():
    """使用tkinter选择文件夹，支持高DPI"""
    # 创建根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 设置高DPI支持
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 打开文件夹选择对话框
    folder_path = filedialog.askdirectory(
        title="请选择包含视频文件的文件夹",
        mustexist=True
    )
    
    root.destroy()  # 销毁窗口
    return folder_path


def get_video_files(directory):
    """获取目录中的所有视频文件（仅首层）"""
    if not os.path.isdir(directory):
        return []

    video_files = []
    # 只扫描第一层级
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and is_video_file(item_path):
            video_files.append(item_path)

    return sorted(video_files)  # 排序以便更好的显示


def convert_to_audio(video_path, format_choice, keep_original):
    """转换视频为音频"""
    # 获取视频文件目录和文件名（不带扩展名）
    directory, filename = os.path.split(video_path)
    filename_without_ext = os.path.splitext(filename)[0]

    # 确定输出格式和ffmpeg参数
    if format_choice == "1":
        # 高品质AAC
        output_format = "aac"
        format_params = ["-c:a", "aac", "-b:a", "320k"]
        format_name = "AAC音频"
    else:
        # 无损FLAC
        output_format = "flac"
        format_params = ["-c:a", "flac"]
        format_name = "FLAC音频"

    # 创建临时文件用于处理
    temp_dir = tempfile.gettempdir()
    temp_input = os.path.join(temp_dir, f"input_{uuid.uuid4().hex}.mp4")
    temp_output = os.path.join(temp_dir, f"output_{uuid.uuid4().hex}.{output_format}")
    final_output = os.path.join(directory, f"{filename_without_ext}.{output_format}")

    try:
        # 复制源文件到临时文件
        print(f"\n正在准备处理 {filename}...")
        shutil.copy2(video_path, temp_input)

        # 构建FFmpeg命令
        print(f"正在将 {filename} 转换为{format_name}...")
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            temp_input,
            "-vn",  # 不要视频流
        ]
        ffmpeg_cmd.extend(format_params)
        ffmpeg_cmd.append(temp_output)

        # 使用subprocess.run执行命令，避免使用Popen循环读取输出
        result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,  # 5分钟超时
        )        # 检查转换结果
        if result.returncode == 0 and os.path.exists(temp_output):            # 复制临时输出文件到最终位置
            shutil.copy2(temp_output, final_output)
            print(f"✅ 转换完成: {os.path.basename(final_output)}")

            # 如果用户选择不保留原视频
            if keep_original == "2":
                os.remove(video_path)
                print(f"🗑️ 已删除原视频文件: {os.path.basename(video_path)}")
            
            return True
        else:
            print(f"❌ 转换失败: {filename}")
            if result.stdout:
                print(f"FFmpeg输出: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ 转换超时: 处理 {filename} 时间过长，已中止")
        return False
    except Exception as e:
        print(f"❌ 转换过程中出错: {e}")
        return False
    finally:
        # 清理临时文件
        for temp_file in [temp_input, temp_output]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:  # noqa: E722
                    pass


def main():
    """简化的主函数，使用图形界面选择文件夹"""
    print("🎬" + "=" * 48)
    print("   视频音频分离工具")  
    print("=" * 50)
    
    # 使用tkinter选择文件夹
    print("📁 请在弹出的窗口中选择包含视频文件的文件夹...")
    target_folder = select_folder_with_tkinter()
    
    if not target_folder:
        print("❌ 未选择文件夹，程序退出")
        return
    
    print(f"📂 选择的文件夹: {target_folder}")
    
    # 获取视频文件列表（仅首层）
    video_files = get_video_files(target_folder)
    
    if not video_files:
        print("❌ 在选择的文件夹中未找到任何视频文件!")
        return
    
    # 显示找到的视频文件
    print(f"\n🎥 找到 {len(video_files)} 个视频文件:")
    for i, video in enumerate(video_files, 1):
        print(f"  {i:2d}. {os.path.basename(video)}")
    
    # 选择要处理的视频（默认全选）
    print(f"\n📋 默认全选所有视频")
    selection_input = input("输入要处理的视频编号(如: 1,3,5)，直接回车全选: ").strip()
    
    selected_videos = []
    if selection_input:
        try:
            indices = [int(idx.strip()) for idx in selection_input.split(",") if idx.strip()]
            for idx in indices:
                if 1 <= idx <= len(video_files):
                    selected_videos.append(video_files[idx - 1])
                else:
                    print(f"⚠️ 编号 {idx} 超出范围，将被忽略")
        except ValueError:
            print("❌ 输入格式错误，将处理所有视频")
            selected_videos = video_files
    else:
        selected_videos = video_files
    
    if not selected_videos:
        print("❌ 没有选择任何视频，程序退出")
        return
    
    print(f"✅ 将处理 {len(selected_videos)} 个视频文件")
    
    # 选择音频格式
    print("\n🎵 请选择输出音频格式:")
    print("  1. AAC (高品质，小文件)")
    print("  2. FLAC (无损，大文件)")
    format_choice = input("请选择 [1/2] (默认AAC): ").strip() or "1"
    
    while format_choice not in ["1", "2"]:
        format_choice = input("❌ 无效选项，请重新选择 [1/2]: ").strip()
    
    format_name = "AAC" if format_choice == "1" else "FLAC"
    print(f"📤 选择格式: {format_name}")
    
    # 开始转换
    print(f"\n🚀 开始转换...")
    start_time = time.time()
    total = len(selected_videos)
    successful = 0
    
    for i, video_path in enumerate(selected_videos, 1):
        print(f"\n[{i}/{total}] 处理: {os.path.basename(video_path)}")
        
        # 转换视频（默认保留原文件）
        if convert_to_audio(video_path, format_choice, "1"):
            successful += 1
    
    # 转换完成报告
    total_duration = time.time() - start_time
    print(f"\n🎉 转换完成!")
    print(f"⏱️  总用时: {total_duration:.1f}秒")
    print(f"📊 处理结果: 共 {total} 个文件，成功 {successful} 个，失败 {total - successful} 个")
    
    if successful > 0:
        print(f"📁 音频文件保存在: {target_folder}")
    
    
if __name__ == "__main__":
    main()
