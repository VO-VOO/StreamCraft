import os
import subprocess
import sys
import shutil
import tempfile
import uuid 
import time


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


def get_video_files(directory):
    """获取目录中的所有视频文件"""
    if os.path.isfile(directory) and is_video_file(directory):
        # 如果输入的是单个视频文件
        return [directory]

    video_files = []
    # 只扫描第一层级
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and is_video_file(item_path):
            video_files.append(item_path)

    return video_files


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
        )

        # 检查转换结果
        if result.returncode == 0 and os.path.exists(temp_output):
            # 复制临时输出文件到最终位置
            shutil.copy2(temp_output, final_output)
            print(f"转换完成: {final_output}")

            # 如果用户选择不保留原视频
            if keep_original == "2":
                os.remove(video_path)
                print(f"已删除原视频文件: {video_path}")
        else:
            print(f"转换失败: {video_path}")
            print(f"FFmpeg输出: {result.stdout}")

    except subprocess.TimeoutExpired:
        print(f"转换超时: 处理 {filename} 时间过长，已中止")
    except Exception as e:
        print(f"转换过程中出错: {e}")
    finally:
        # 清理临时文件
        for temp_file in [temp_input, temp_output]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:  # noqa: E722
                    pass


def main():
    # 确保脚本使用UTF-8编码处理所有文本
    if sys.stdout.encoding.lower() != "utf-8":
        try:
            # 尝试将控制台编码设置为UTF-8
            sys.stdout.reconfigure(encoding="utf-8") # type: ignore
        except AttributeError:
            # Python 3.6及更早版本不支持reconfigure
            pass

    print("=" * 50)

    # 获取目标路径
    target_path = input("请输入目标文件夹路径或视频文件路径: ").strip('"')

    if not os.path.exists(target_path):
        print(f"错误: 路径 '{target_path}' 不存在!")
        return

    # 获取视频文件列表
    video_files = get_video_files(target_path)

    if not video_files:
        print("未找到任何视频文件!")
        return

    # 显示找到的视频文件
    print(f"\n找到 {len(video_files)} 个视频文件:")
    for i, video in enumerate(video_files, 1):
        print(f"{i}. {os.path.basename(video)}")

    # 询问是否只处理特定视频
    choice = input("\n是否只处理部分视频? (Y/N, 默认N): ").strip().upper()
    selected_videos = []

    if choice == "Y":
        indices_input = input("请输入视频编号(如1,3,5): ").strip()
        try:
            indices = [
                int(idx.strip()) for idx in indices_input.split(",") if idx.strip()
            ]
            for idx in indices:
                if 1 <= idx <= len(video_files):
                    selected_videos.append(video_files[idx - 1])
                else:
                    print(f"警告: 编号 {idx} 超出范围，将被忽略")
        except ValueError:
            print("输入格式错误，将处理所有视频")
            selected_videos = video_files
    else:
        selected_videos = video_files

    if not selected_videos:
        print("没有选择任何视频，操作取消")
        return

    # 询问转换格式
    print("\n请选择转换格式:")
    print("1. 高品质AAC音频 (默认)")
    print("2. 无损FLAC音频")
    format_choice = input("请输入选项编号 [1/2]: ").strip() or "1"  # 默认选择AAC

    while format_choice not in ["1", "2"]:
        format_choice = input("无效选项，请重新输入 [1/2]: ").strip()

    # 询问是否保留原视频
    print("\n是否保留原视频文件:")
    print("1. 是（默认）")
    print("2. 否")
    keep_original = input("请输入选项编号 [1/2]: ").strip() or "1"  # 默认保留

    while keep_original not in ["1", "2"]:
        keep_original = input("无效选项，请重新输入 [1/2]: ").strip()

    # 开始转换
    start_time = time.time()
    total = len(selected_videos)
    successful = 0

    print("\n===== 开始转换 =====")
    for i, video_path in enumerate(selected_videos, 1):
        print(f"\n[{i}/{total}] 处理文件 {os.path.basename(video_path)}")
        file_start = time.time()

        convert_to_audio(video_path, format_choice, keep_original)

        # 检查是否创建了输出文件
        output_format = "m4a" if format_choice == "1" else "flac"
        expected_output = os.path.splitext(video_path)[0] + f".{output_format}"
        if os.path.exists(expected_output):
            successful += 1

        file_duration = time.time() - file_start
        print(f"处理用时: {file_duration:.1f}秒")

    # 汇总报告
    total_duration = time.time() - start_time
    print("\n===== 转换完成 =====")
    print(f"总用时: {total_duration:.1f}秒")
    print(
        f"处理结果: 共 {total} 个文件，成功 {successful} 个，失败 {total - successful} 个"
    )


if __name__ == "__main__":
    main()
