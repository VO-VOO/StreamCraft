import gradio as gr
import os
import sys
import subprocess
import json
import time
import tempfile
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


# 导入原有功能
def is_video_file(file_path):
    """判断文件是否为视频文件"""
    video_extensions = [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", 
        ".m4v", ".mpg", ".mpeg", ".3gp"
    ]
    _, ext = os.path.splitext(file_path)
    return ext.lower() in video_extensions


def get_video_files(directory):
    """获取目录中的所有视频文件"""
    if os.path.isfile(directory) and is_video_file(directory):
        return [directory]

    video_files = []
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and is_video_file(item_path):
                video_files.append(item_path)
    except (PermissionError, FileNotFoundError):
        pass
    
    return video_files


def check_cookies_file() -> Tuple[bool, str]:
    """检查cookies文件状态"""
    # cookies文件在当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_path = os.path.join(script_dir, "cookies.txt")
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line for line in content.split('\n') if line.strip() and not line.startswith('#')]
                return True, f"✅ Cookies文件已加载，包含 {len(lines)} 条记录"
        except Exception as e:
            return False, f"❌ Cookies文件读取失败: {str(e)}"
    else:
        return False, "⚠️ 未找到cookies.txt文件，某些网站可能无法访问"


def check_playlist(url):
    """检查URL是否为视频合集"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", url], 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=30
        )
        
        output_lines = result.stdout.strip().split('\n')
        if len(output_lines) > 1:
            return True, output_lines
        else:
            return False, []
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
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


def create_timestamped_folder():
    """创建以当前时间命名的文件夹"""
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # 确保下载到C:\Users\chenw\Videos目录
    download_base_dir = r"C:\Users\chenw\Videos"
    folder_name = os.path.join(download_base_dir, f"下载_{current_time}")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name


def convert_to_audio(video_path, format_choice, keep_original, progress=gr.Progress()):
    """转换视频为音频"""
    directory, filename = os.path.split(video_path)
    filename_without_ext = os.path.splitext(filename)[0]

    if format_choice == "AAC":
        output_format = "aac"
        format_params = ["-c:a", "aac", "-b:a", "320k"]
        format_name = "AAC音频"
    else:
        output_format = "flac"
        format_params = ["-c:a", "flac"]
        format_name = "FLAC音频"

    temp_dir = tempfile.gettempdir()
    temp_input = os.path.join(temp_dir, f"input_{uuid.uuid4().hex}.mp4")
    temp_output = os.path.join(temp_dir, f"output_{uuid.uuid4().hex}.{output_format}")
    final_output = os.path.join(directory, f"{filename_without_ext}.{output_format}")

    try:
        progress(0.1, desc=f"准备处理 {filename}...")
        shutil.copy2(video_path, temp_input)

        progress(0.3, desc=f"转换为{format_name}...")
        ffmpeg_cmd = ["ffmpeg", "-i", temp_input, "-vn"] + format_params + [temp_output]
        
        result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            timeout=300
        )

        progress(0.8, desc="完成转换...")
        if result.returncode == 0 and os.path.exists(temp_output):
            shutil.copy2(temp_output, final_output)
            
            if not keep_original:
                os.remove(video_path)
                
            progress(1.0, desc="转换完成!")
            return True, f"✅ 转换完成: {final_output}"
        else:
            return False, f"❌ 转换失败: {result.stdout}"

    except subprocess.TimeoutExpired:
        return False, f"❌ 转换超时: 处理 {filename} 时间过长"
    except Exception as e:
        return False, f"❌ 转换出错: {str(e)}"
    finally:
        for temp_file in [temp_input, temp_output]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


# Gradio界面函数
def analyze_url(url):
    """分析URL，返回视频信息"""
    if not url.strip():
        return "请输入有效的URL", [], ""
    
    cookies_exists, cookies_status = check_cookies_file()
    
    try:
        is_playlist, output_lines = check_playlist(url)
        
        if is_playlist and output_lines:
            videos = get_playlist_videos(output_lines)
            if videos:
                video_list = [f"{i+1}. {video['title']}" for i, video in enumerate(videos)]
                return (
                    f"🎬 检测到视频合集，共 {len(videos)} 个视频\n{cookies_status}",
                    video_list,
                    json.dumps(videos)  # 存储视频数据
                )
            else:
                return f"❌ 无法解析合集内容\n{cookies_status}", [], ""
        else:
            return f"📹 检测到单个视频\n{cookies_status}", [], ""
    
    except Exception as e:
        return f"❌ 分析失败: {str(e)}\n{cookies_status}", [], ""


def download_videos(url, video_data_json, selected_videos, auto_extract_audio, audio_format, keep_original):
    """下载视频"""
    if not url.strip():
        return "❌ 请先输入URL并分析"
    
    try:
        download_folder = create_timestamped_folder()
        # cookies文件在当前脚本目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_path = os.path.join(script_dir, "cookies.txt")
        results = []
        
        if video_data_json:
            # 处理视频合集
            videos = json.loads(video_data_json)
            if not selected_videos:
                return "❌ 请选择要下载的视频"
            
            # 解析选择的视频索引
            selected_indices = []
            for selection in selected_videos:
                try:
                    idx = int(selection.split('.')[0]) - 1
                    if 0 <= idx < len(videos):
                        selected_indices.append(idx)
                except:
                    continue
            
            if not selected_indices:
                return "❌ 没有有效的视频选择"
            
            results.append(f"📁 下载文件夹: {download_folder}")
            
            for i, idx in enumerate(selected_indices):
                video = videos[idx]
                results.append(f"\n[{i+1}/{len(selected_indices)}] 下载: {video['title']}")
                
                download_cmd = ["yt-dlp"]
                if os.path.exists(cookies_path):
                    download_cmd.extend(["--cookies", cookies_path])
                download_cmd.extend([
                    "-o", os.path.join(download_folder, "%(title)s.%(ext)s"),
                    video['url']
                ])
                
                try:
                    result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=600)
                    if result.returncode == 0:
                        results.append("✅ 下载成功")
                        
                        # 自动音频提取
                        if auto_extract_audio:
                            video_files = get_video_files(download_folder)
                            for video_file in video_files:
                                if video['title'].replace('/', '_') in os.path.basename(video_file):
                                    success, msg = convert_to_audio(video_file, audio_format, keep_original)
                                    results.append(f"🎵 音频提取: {msg}")
                                    break
                    else:
                        results.append(f"❌ 下载失败: {result.stderr}")
                except subprocess.TimeoutExpired:
                    results.append("❌ 下载超时")
                except Exception as e:
                    results.append(f"❌ 下载出错: {str(e)}")
        
        else:
            # 处理单个视频
            results.append(f"📁 下载文件夹: {download_folder}")
            results.append("📹 下载单个视频...")
            
            download_cmd = ["yt-dlp"]
            if os.path.exists(cookies_path):
                download_cmd.extend(["--cookies", cookies_path])
            download_cmd.extend([
                "-o", os.path.join(download_folder, "%(title)s.%(ext)s"),
                url
            ])
            
            try:
                result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=600)
                if result.returncode == 0:
                    results.append("✅ 下载成功")
                    
                    # 自动音频提取
                    if auto_extract_audio:
                        video_files = get_video_files(download_folder)
                        for video_file in video_files:
                            success, msg = convert_to_audio(video_file, audio_format, keep_original)
                            results.append(f"🎵 音频提取: {msg}")
                else:
                    results.append(f"❌ 下载失败: {result.stderr}")
            except subprocess.TimeoutExpired:
                results.append("❌ 下载超时")
            except Exception as e:
                results.append(f"❌ 下载出错: {str(e)}")
        
        return "\n".join(results)
    
    except Exception as e:
        return f"❌ 处理失败: {str(e)}"


def batch_audio_extract(folder_path, selected_videos, audio_format, keep_original):
    """批量音频提取"""
    if not folder_path or not os.path.exists(folder_path):
        return "❌ 请选择有效的文件夹路径"
    
    video_files = get_video_files(folder_path)
    if not video_files:
        return "❌ 文件夹中没有找到视频文件"
    
    results = []
    results.append(f"📁 处理文件夹: {folder_path}")
    results.append(f"🎬 找到 {len(video_files)} 个视频文件")
    
    # 如果有选择特定视频
    if selected_videos:
        selected_indices = []
        for selection in selected_videos:
            try:
                idx = int(selection.split('.')[0]) - 1
                if 0 <= idx < len(video_files):
                    selected_indices.append(idx)
            except:
                continue
        
        if selected_indices:
            video_files = [video_files[i] for i in selected_indices]
            results.append(f"✅ 已选择 {len(video_files)} 个视频进行处理")
    
    successful = 0
    for i, video_path in enumerate(video_files, 1):
        results.append(f"\n[{i}/{len(video_files)}] 处理: {os.path.basename(video_path)}")
        
        success, msg = convert_to_audio(video_path, audio_format, keep_original)
        results.append(msg)
        if success:
            successful += 1
    
    results.append(f"\n📊 处理完成: 成功 {successful}/{len(video_files)} 个文件")
    return "\n".join(results)


def get_folder_videos(folder_path):
    """获取文件夹中的视频列表"""
    if not folder_path or not os.path.exists(folder_path):
        return []
    
    video_files = get_video_files(folder_path)
    return [f"{i+1}. {os.path.basename(video)}" for i, video in enumerate(video_files)]


# 创建Gradio界面
def create_interface():
    # 自定义CSS样式 - 深色主题
    custom_css = """
    /* 深色主题样式 */
    .gradio-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
        color: #e0e0e0 !important;
    }
    
    .gradio-container .gradio-tabs {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .gradio-container .gradio-tab {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #e0e0e0 !important;
        border-radius: 10px !important;
        margin: 5px !important;
        transition: all 0.3s ease !important;
    }
    
    .gradio-container .gradio-tab:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        transform: translateY(-2px) !important;
    }
    
    .gradio-container .gradio-tab.selected {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    .gradio-container .gradio-textbox, 
    .gradio-container .gradio-dropdown,
    .gradio-container .gradio-checkbox-group {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
    }
    
    .gradio-container .gradio-button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        color: white !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    .gradio-container .gradio-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    .gradio-container .gradio-button.primary {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a52 100%) !important;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4) !important;
    }
    
    .gradio-container .gradio-button.primary:hover {
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6) !important;
    }
    
    .gradio-container h1, h2, h3 {
        color: #e0e0e0 !important;
        text-align: center !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5) !important;
    }
    
    .gradio-container .markdown {
        color: #e0e0e0 !important;
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        padding: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    """
    
    with gr.Blocks(css=custom_css, title="🎬 媒体处理工具", theme=gr.themes.Glass()) as demo: # type: ignore
        gr.Markdown(
            """
            # 🎬 媒体处理工具
            ### 强大的视频下载和音频提取工具
            支持各大视频网站下载，批量音频提取
            """,
            elem_classes=["markdown"]
        )
        
        with gr.Tabs():
            # 视频下载标签页
            with gr.Tab("📥 视频下载器", elem_classes=["gradio-tab"]):
                with gr.Row():
                    with gr.Column(scale=2):
                        url_input = gr.Textbox(
                            label="🔗 视频URL",
                            placeholder="请输入视频链接 (支持YouTube, B站等)",
                            elem_classes=["gradio-textbox"]
                        )
                        
                        analyze_btn = gr.Button(
                            "🔍 分析视频",
                            variant="primary",
                            elem_classes=["gradio-button primary"]
                        )
                        
                        with gr.Row():
                            auto_extract = gr.Checkbox(
                                label="📱 下载后自动提取音频",
                                value=False
                            )
                            audio_format_dl = gr.Dropdown(
                                choices=["AAC", "FLAC"],
                                value="AAC",
                                label="🎵 音频格式",
                                elem_classes=["gradio-dropdown"]
                            )
                            keep_original_dl = gr.Checkbox(
                                label="💾 保留原视频",
                                value=True
                            )
                    
                    with gr.Column(scale=1):
                        cookies_status = gr.Markdown("🔄 等待分析...")
                
                with gr.Row():
                    video_list = gr.CheckboxGroup(
                        label="📋 选择要下载的视频",
                        choices=[],
                        elem_classes=["gradio-checkbox-group"]
                    )
                
                download_btn = gr.Button(
                    "⬇️ 开始下载",
                    size="lg",
                    elem_classes=["gradio-button"]
                )
                
                download_output = gr.Textbox(
                    label="📊 下载状态",
                    lines=10,
                    max_lines=20,
                    elem_classes=["gradio-textbox"]
                )
                
                # 隐藏的数据存储
                video_data = gr.Textbox(visible=False)
            
            # 音频提取标签页
            with gr.Tab("🎵 音频提取器", elem_classes=["gradio-tab"]):
                with gr.Row():
                    with gr.Column():
                        folder_input = gr.Textbox(
                            label="📁 视频文件夹路径",
                            placeholder="请输入包含视频文件的文件夹路径",
                            elem_classes=["gradio-textbox"]
                        )
                        
                        refresh_btn = gr.Button(
                            "🔄 刷新视频列表",
                            elem_classes=["gradio-button"]
                        )
                        
                        with gr.Row():
                            audio_format_ex = gr.Dropdown(
                                choices=["AAC", "FLAC"],
                                value="AAC",
                                label="🎵 音频格式",
                                elem_classes=["gradio-dropdown"]
                            )
                            keep_original_ex = gr.Checkbox(
                                label="💾 保留原视频",
                                value=True
                            )
                
                video_list_extract = gr.CheckboxGroup(
                    label="📋 选择要提取音频的视频（不选择则处理全部）",
                    choices=[],
                    elem_classes=["gradio-checkbox-group"]
                )
                
                extract_btn = gr.Button(
                    "🎵 开始提取音频",
                    size="lg",
                    elem_classes=["gradio-button"]
                )
                
                extract_output = gr.Textbox(
                    label="📊 提取状态",
                    lines=10,
                    max_lines=20,
                    elem_classes=["gradio-textbox"]
                )
        
        # 事件绑定
        analyze_btn.click(
            fn=analyze_url,
            inputs=[url_input],
            outputs=[cookies_status, video_list, video_data]
        )
        
        download_btn.click(
            fn=download_videos,
            inputs=[url_input, video_data, video_list, auto_extract, audio_format_dl, keep_original_dl],
            outputs=[download_output]
        )
        
        refresh_btn.click(
            fn=get_folder_videos,
            inputs=[folder_input],
            outputs=[video_list_extract]
        )
        
        extract_btn.click(
            fn=batch_audio_extract,
            inputs=[folder_input, video_list_extract, audio_format_ex, keep_original_ex],
            outputs=[extract_output]
        )
    
    return demo


if __name__ == "__main__":
    # 检查依赖
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误: 未找到 yt-dlp，请先安装")
        print("安装命令: pip install yt-dlp")
        sys.exit(1)
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误: 未找到 ffmpeg，请先安装")
        print("Windows: 下载 https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # 启动界面
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        show_error=True
    )
