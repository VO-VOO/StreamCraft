import subprocess
import os
import json
import sys
from datetime import datetime
from video_title_fetcher import enhance_video_titles

def get_python_executable():
    """获取当前Python解释器的完整路径"""
    return sys.executable

def get_download_path():
    """从config.json获取下载路径"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('download_path', r"C:\Users\chenw\Videos")
        else:
            return r"C:\Users\chenw\Videos"
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return r"C:\Users\chenw\Videos"

def check_playlist(url):
    """检查URL是否为视频合集"""
    try:
        print("正在检查是否为视频合集...")
        python_exe = get_python_executable()
        result = subprocess.run(
            [python_exe, "-m", "yt_dlp", "--flat-playlist", "--dump-json", url], 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=30  # 添加超时时间
        )
        
        # 解析输出以确定是否为合集
        output_lines = result.stdout.strip().split('\n')
        print(f"yt-dlp返回了 {len(output_lines)} 行数据")
        
        # 过滤空行
        output_lines = [line for line in output_lines if line.strip()]
        print(f"过滤空行后有 {len(output_lines)} 行有效数据")
        
        if len(output_lines) > 1:
            # 有多行JSON输出，说明是合集
            print("检测到视频合集")
            return True, output_lines
        else:
            # 只有单个视频
            print("检测到单个视频")
            return False, []
    except subprocess.CalledProcessError as e:
        # 命令执行失败
        print(f"yt-dlp命令执行失败: {e}")
        return False, []
    except subprocess.TimeoutExpired:
        print("yt-dlp命令执行超时")
        return False, []

def get_playlist_videos(output_lines):
    """从yt-dlp输出中解析视频信息（仅解析基础信息，不处理标题）"""
    videos = []
    for i, line in enumerate(output_lines):
        try:
            if line.strip():  # 确保行不为空
                video_info = json.loads(line)
                
                # 只解析基础信息，标题处理交给 video_title_fetcher
                playlist_title = video_info.get('playlist_title', '')
                playlist_index = video_info.get('playlist_index', i+1)
                
                videos.append({
                    'title': video_info.get('title', f'视频_{playlist_index}'),  # 临时标题
                    'id': video_info.get('id', ''),
                    'url': video_info.get('webpage_url', '') or video_info.get('url', ''),
                    'playlist_index': playlist_index,
                    'playlist_title': playlist_title
                })
        except json.JSONDecodeError:
            continue
        except Exception:
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

def create_download_folder(use_timestamp=True, base_path=None):
    """创建下载文件夹"""
    if base_path is None:
        base_path = get_download_path()
    
    if use_timestamp:
        # 使用时间戳子文件夹（命令行模式）
        current_time = datetime.now().strftime("%Y-%m-%d %H：%M")
        download_folder = os.path.join(base_path, current_time)
    else:
        # 直接使用配置路径（Web界面模式）
        download_folder = base_path
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    return download_folder

def download_videos(url, videos=None, selected_indices=None, cookies_path=None, use_timestamp=True):
    """
    下载视频
    
    Args:
        url: 视频URL
        videos: 视频列表（用于合集）
        selected_indices: 选定的视频索引（用于合集）
        cookies_path: cookies文件路径
        use_timestamp: 是否使用时间戳文件夹（Web界面传False）
    """
    try:
        # 创建下载文件夹
        download_folder = create_download_folder(use_timestamp=use_timestamp)
        print(f"将下载视频到文件夹: {download_folder}")
        
        # 获取正确的Python解释器路径
        python_exe = get_python_executable()
        
        if videos and selected_indices:
            # 下载选定的视频
            for idx in selected_indices:
                if 0 <= idx < len(videos):
                    video = videos[idx]
                    print(f"\n正在下载: {video['title']}")
                    
                    # 构建下载命令，使用正确的Python解释器
                    download_cmd = [python_exe, "-m", "yt_dlp"]
                    
                    # 添加cookies
                    if cookies_path and os.path.exists(cookies_path):
                        download_cmd.extend(["--cookies", cookies_path])
                    
                    # 优化的清晰度选择策略：优先1080p，然后向下寻找最高可用清晰度
                    # 新的格式选择逻辑：
                    # 1. 首选1080p (height=1080)
                    # 2. 如果没有1080p，选择小于等于1080p的最高清晰度
                    # 3. 确保音视频都有
                    format_selector = (
                        "bestvideo[height=1080]+bestaudio/bestvideo[height<=1080]+bestaudio/"
                        "best[height=1080]/best[height<=1080]/best"
                    )
                    download_cmd.extend(["-f", format_selector])
                    
                    # 输出格式
                    download_cmd.extend([
                        "-o", os.path.join(download_folder, "%(title)s.%(ext)s"),
                        "--merge-output-format", "mp4",
                        "--embed-thumbnail",
                        video['url']
                    ])
                    
                    subprocess.run(download_cmd, check=True)
            
            print("所选视频下载完成！")
        else:
            # 下载单个视频            print(f"\n正在下载单个视频: {url}")
            
            # 构建下载命令，使用正确的Python解释器
            download_cmd = [python_exe, "-m", "yt_dlp"]
            
            # 添加cookies
            if cookies_path and os.path.exists(cookies_path):
                download_cmd.extend(["--cookies", cookies_path])
            
            # 优化的清晰度选择策略：优先1080p，然后向下寻找最高可用清晰度
            # 新的格式选择逻辑：
            # 1. 首选1080p (height=1080)
            # 2. 如果没有1080p，选择小于等于1080p的最高清晰度
            # 3. 确保音视频都有
            format_selector = (
                "bestvideo[height=1080]+bestaudio/bestvideo[height<=1080]+bestaudio/"
                "best[height=1080]/best[height<=1080]/best"
            )
            download_cmd.extend(["-f", format_selector])
            
            # 输出格式
            download_cmd.extend([
                "-o", os.path.join(download_folder, "%(title)s.%(ext)s"),
                "--merge-output-format", "mp4",
                "--embed-thumbnail",
                url
            ])
            
            subprocess.run(download_cmd, check=True)
            print("下载完成！")
    except subprocess.CalledProcessError as e:
        print(f"下载过程中出错：{e}")

def main():
    """命令行主函数"""
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
                download_videos(url, cookies_path=cookies_path, use_timestamp=True)
                return
            
            # 获取真实视频标题（使用标题模块）
            print("\n正在获取视频标题...")
            videos = enhance_video_titles(videos, url, cookies_path)
            
            print(f"\n检测到视频合集，共 {len(videos)} 个视频:")
            for i, video in enumerate(videos):
                print(f"{i+1}. {video['title']}")
            
            choice = input("\n请输入要下载的视频序号（如：1,3,5），直接回车下载全部: ")
            
            if choice.strip():
                # 解析用户输入的序号
                try:
                    # 将输入的序号转换为索引（减1，因为展示给用户时是从1开始的）
                    selected_indices = [int(idx.strip()) - 1 for idx in choice.split(',') if idx.strip()]
                    download_videos(url, videos, selected_indices, cookies_path, use_timestamp=True)
                except ValueError:
                    print("输入格式错误，请输入数字，用逗号分隔。")
            else:
                # 下载全部视频
                download_videos(url, videos, list(range(len(videos))), cookies_path, use_timestamp=True)
        else:
            # 单个视频，获取标题并下载
            print("\n正在获取单个视频标题...")
            # 创建一个只包含单个视频的列表，传递给enhance_video_titles
            single_video = [{
                'title': '视频',
                'url': url,
                'playlist_index': 1,
                'playlist_title': ''
            }]
            
            # 使用video_title_fetcher获取准确标题
            enhanced_videos = enhance_video_titles(single_video, url, cookies_path)
            
            if enhanced_videos and enhanced_videos[0].get('title'):
                print(f"\n获取到视频标题: {enhanced_videos[0]['title']}")
                # 使用增强后的视频信息下载
                download_videos(url, enhanced_videos, [0], cookies_path, use_timestamp=True)
            else:
                print("\n无法获取视频标题，使用默认方式下载")
                download_videos(url, cookies_path=cookies_path, use_timestamp=True)
    except FileNotFoundError:
        print("yt-dlp未安装或没有添加到环境变量中。")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
