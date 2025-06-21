import subprocess
import os
import json
from datetime import datetime

def check_playlist(url):
    """检查URL是否为视频合集"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", url], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # 解析输出以确定是否为合集
        output_lines = result.stdout.strip().split('\n')
        if len(output_lines) > 1:
            # 有多行JSON输出，说明是合集
            return True, output_lines
        else:
            # 只有单个视频
            return False, []
    except subprocess.CalledProcessError:
        # 命令执行失败
        return False, []

def get_playlist_videos(output_lines):
    """从yt-dlp输出中解析视频信息"""
    videos = []
    for line in output_lines:
        try:
            video_info = json.loads(line)
            title = video_info.get('title', '未知标题')
            videos.append({
                'title': title,
                'id': video_info.get('id', ''),
                'url': video_info.get('webpage_url', '') or video_info.get('url', '')
            })
        except json.JSONDecodeError:
            continue
    return videos

def sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    # 移除URL中的查询参数
    filename = filename.split('?')[0]
    # 移除Windows文件名中不允许的字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def create_timestamped_folder():
    """创建以当前时间命名的文件夹"""
    current_time = datetime.now().strftime("%Y-%m-%d %H：%M")
    folder_name = current_time
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def download_videos(url, videos=None, selected_indices=None, cookies_path=None):
    """下载视频"""
    try:
        # 创建以当前时间命名的文件夹
        download_folder = create_timestamped_folder()
        print(f"将下载视频到文件夹: {download_folder}")
        
        if videos and selected_indices:
            # 下载选定的视频
            for idx in selected_indices:
                if 0 <= idx < len(videos):
                    video = videos[idx]
                    print(f"\n正在下载: {video['title']}")
                    download_cmd = ["yt-dlp"]
                    if cookies_path and os.path.exists(cookies_path):
                        download_cmd.extend(["--cookies", cookies_path])
                    download_cmd.extend(["-o", os.path.join(download_folder, "%(title)s.%(ext)s"), video['url']])
                    subprocess.run(download_cmd, check=True)
            
            print("所选视频下载完成！")
        else:
            # 下载单个视频
            download_cmd = ["yt-dlp"]
            if cookies_path and os.path.exists(cookies_path):
                download_cmd.extend(["--cookies", cookies_path])
            download_cmd.extend(["-o", os.path.join(download_folder, "%(title)s.%(ext)s"), url])
            subprocess.run(download_cmd, check=True)
            print("下载完成！")
    except subprocess.CalledProcessError as e:
        print(f"下载过程中出错：{e}")

def main():
    # 获取当前目录
    current_dir = os.getcwd()
    
    # 提示用户输入URL
    url = input("请输入要下载的视频URL: ")
    
    # 构建cookies路径
    cookies_path = os.path.join(current_dir, "cookies.txt")
    
    try:
        # 检查是否为合集
        is_playlist, output_lines = check_playlist(url)
        
        if is_playlist and output_lines:
            videos = get_playlist_videos(output_lines)
            
            if not videos:
                print("无法解析合集中的视频，将尝试直接下载...")
                download_videos(url, cookies_path=cookies_path)
                return
            
            print(f"\n检测到视频合集，共 {len(videos)} 个视频:")
            for i, video in enumerate(videos):
                print(f"{i+1}. {video['title']}")
            
            choice = input("\n请输入要下载的视频序号（如：1,3,5），直接回车下载全部: ")
            
            if choice.strip():
                # 解析用户输入的序号
                try:
                    # 将输入的序号转换为索引（减1，因为展示给用户时是从1开始的）
                    selected_indices = [int(idx.strip()) - 1 for idx in choice.split(',') if idx.strip()]
                    download_videos(url, videos, selected_indices, cookies_path)
                except ValueError:
                    print("输入格式错误，请输入数字，用逗号分隔。")
            else:
                # 下载全部视频
                download_videos(url, videos, list(range(len(videos))), cookies_path)
        else:
            # 单个视频，直接下载
            download_videos(url, cookies_path=cookies_path)
    except FileNotFoundError:
        print("yt-dlp未安装或没有添加到环境变量中。")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
