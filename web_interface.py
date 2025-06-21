import gradio as gr
import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import threading
import queue

# 导入 dlp下载器.py 的函数
from dlp下载器 import check_playlist, get_playlist_videos, download_videos, get_python_executable
from video_title_fetcher import enhance_video_titles


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


def check_cookies_status():
    """检查cookies文件状态"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookies_path = os.path.join(script_dir, "cookies.txt")
    
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line for line in content.split('\n') if line.strip() and not line.startswith('#')]
                return f"✅ Cookies文件已加载，包含 {len(lines)} 条记录"
        except Exception:
            return "❌ Cookies文件读取失败"
    else:
        return "⚠️ 未找到cookies.txt文件，某些网站可能无法访问"


def analyze_video_url(url):
    """分析视频URL，获取视频列表"""
    if not url.strip():
        return (
            get_download_path(),
            check_cookies_status(),
            "⚠️ 请输入有效的URL",
            [],
            "",
            []  # 空的默认选择
        )
    
    try:
        print(f"🔍 开始分析URL: {url}")
        
        # 使用 dlp下载器.py 的函数检查是否为合集
        is_playlist, output_lines = check_playlist(url)
        
        if is_playlist and output_lines:
            print("📋 检测到视频合集，正在解析...")
            
            # 获取基础视频信息
            videos = get_playlist_videos(output_lines)
            
            if not videos:
                return (
                    get_download_path(),
                    check_cookies_status(),
                    "❌ 无法解析合集内容",
                    [],
                    "",
                    []  # 空的默认选择
                )
            
            print(f"📊 解析到 {len(videos)} 个视频，正在获取真实标题...")
            
            # 获取cookies路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cookies_path = os.path.join(script_dir, "cookies.txt")
            
            # 使用 enhance_video_titles 获取真实标题
            enhanced_videos = enhance_video_titles(videos, url, cookies_path)
            
            # 准备视频列表用于界面显示
            video_choices = []
            for i, video in enumerate(enhanced_videos):
                choice_text = f"{i+1}. {video['title']}"
                video_choices.append(choice_text)
            
            video_info = f"🎬 检测到视频合集，共 {len(enhanced_videos)} 个视频"
            
            print(f"✅ 成功获取 {len(enhanced_videos)} 个视频的标题")
            
            return (
                get_download_path(),
                check_cookies_status(),
                video_info,
                video_choices,
                json.dumps(enhanced_videos),  # 存储完整的视频数据
                video_choices  # 默认全选
            )
            
        else:
            print("📹 检测到单个视频，正在获取标题...")
            
            # 单个视频处理
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cookies_path = os.path.join(script_dir, "cookies.txt")
            
            # 创建单个视频的数据结构
            single_video = [{
                'title': '视频',
                'url': url,
                'playlist_index': 1,
                'playlist_title': ''
            }]
            
            # 获取真实标题
            enhanced_videos = enhance_video_titles(single_video, url, cookies_path)
            
            if enhanced_videos and enhanced_videos[0].get('title'):
                video_title = enhanced_videos[0]['title']
                video_info = f"📹 单个视频: {video_title}"
                video_choices = [f"1. {video_title}"]
                
                print(f"✅ 获取到视频标题: {video_title}")
                
                return (
                    get_download_path(),
                    check_cookies_status(),
                    video_info,
                    video_choices,
                    json.dumps(enhanced_videos),
                    video_choices  # 默认选中
                )
            else:
                return (
                    get_download_path(),
                    check_cookies_status(),
                    "📹 检测到单个视频（无法获取标题）",
                    [],
                    "",
                    []  # 空的默认选择
                )
                
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return (
            get_download_path(),
            check_cookies_status(),
            f"❌ 分析失败: {str(e)}",
            [],
            "",
            []  # 空的默认选择
        )


def select_all_videos(video_selection_choices):
    """全选所有视频"""
    return video_selection_choices


def clear_all_selections():
    """清空所有选择"""
    return []


def download_selected_videos(url, video_data_json, selected_videos, auto_extract_audio, audio_format, keep_original):
    """下载选中的视频"""
    if not url.strip():
        return "❌ 请先输入URL并分析"
    
    if not video_data_json:
        return "❌ 没有视频数据，请先分析URL"
    
    try:
        # 解析视频数据
        videos = json.loads(video_data_json)
        
        if not selected_videos:
            return "❌ 请选择要下载的视频"
        
        # 将选择的视频标题转换为索引
        selected_indices = []
        for selected_title in selected_videos:
            # 提取序号（格式: "1. 视频标题"）
            try:
                index_str = selected_title.split('.')[0]
                index = int(index_str) - 1  # 转换为0基础索引
                if 0 <= index < len(videos):
                    selected_indices.append(index)
            except (ValueError, IndexError):
                continue
        
        if not selected_indices:
            return "❌ 没有有效的视频选择"
        
        print(f"🚀 开始下载 {len(selected_indices)} 个视频...")
        
        # 获取cookies路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_path = os.path.join(script_dir, "cookies.txt")
        
        # 使用 dlp下载器.py 的下载函数
        result_queue = queue.Queue()
        
        def download_thread():
            try:
                # 调用 dlp下载器.py 的下载函数
                download_videos(url, videos, selected_indices, cookies_path)
                result_queue.put("✅ 下载完成！")
            except Exception as e:
                result_queue.put(f"❌ 下载失败: {str(e)}")
        
        # 在新线程中执行下载，避免阻塞界面
        thread = threading.Thread(target=download_thread)
        thread.start()
        
        # 等待下载完成（最多等待30秒显示初始状态）
        try:
            result = result_queue.get(timeout=30)
            return result
        except queue.Empty:
            return "🔄 下载正在进行中...（请查看终端输出获取详细进度）"
            
    except Exception as e:
        return f"❌ 处理失败: {str(e)}"


def create_interface():
    """创建Gradio界面"""
    
    # 自定义CSS样式
    custom_css = """
    .gradio-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
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
    
    .gradio-container .gradio-textbox, 
    .gradio-container .gradio-dropdown,
    .gradio-container .gradio-checkbox-group {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
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
        
        with gr.Row():
            # 左侧主要操作区域
            with gr.Column(scale=3):
                # 视频URL输入
                url_input = gr.Textbox(
                    label="🔗 视频URL",
                    placeholder="请输入视频链接 (支持YouTube, B站等)",
                    elem_classes=["gradio-textbox"]
                )
                
                # 分析按钮
                analyze_btn = gr.Button(
                    "🔍 分析视频",
                    variant="primary",
                    elem_classes=["gradio-button primary"]
                )
                
                # 下载选项
                with gr.Row():
                    with gr.Column():
                        auto_extract = gr.Checkbox(
                            label="📱 下载后自动提取音频",
                            value=False
                        )
                        keep_original = gr.Checkbox(
                            label="💾 保留原视频",
                            value=True
                        )
                    with gr.Column():
                        audio_format = gr.Dropdown(
                            choices=["AAC", "FLAC"],
                            value="AAC",
                            label="🎵 音频格式",
                            elem_classes=["gradio-dropdown"]
                        )
                    with gr.Column():
                        download_btn = gr.Button(
                            "⬇️ 下载视频",
                            size="lg",
                            elem_classes=["gradio-button"]
                        )
            
            # 右侧信息显示区域
            with gr.Column(scale=1):
                # 下载路径
                download_path_display = gr.Textbox(
                    label="📁 下载路径",
                    value=get_download_path(),
                    interactive=False,
                    elem_classes=["gradio-textbox"]
                )
                
                # Cookies状态
                cookies_status_display = gr.Textbox(
                    label="🍪 Cookies状态",
                    value=check_cookies_status(),
                    interactive=False,
                    elem_classes=["gradio-textbox"]
                )
                
                # 视频信息
                video_info_display = gr.Textbox(
                    label="📺 视频信息",
                    value="🔄 等待分析...",
                    interactive=False,
                    elem_classes=["gradio-textbox"]
                )
                
                # 下载状态
                download_status = gr.Textbox(
                    label="📊 下载状态",
                    lines=8,
                    max_lines=12,
                    elem_classes=["gradio-textbox"]
                )
        
        # 视频选择区域
        with gr.Row():
            with gr.Column(scale=4):
                video_selection = gr.CheckboxGroup(
                    label="📋 选择要下载的视频",
                    choices=[],
                    value=[],
                    elem_classes=["gradio-checkbox-group"]
                )
            with gr.Column(scale=1):
                select_all_btn = gr.Button(
                    "✅ 全选",
                    elem_classes=["gradio-button"]
                )
                clear_all_btn = gr.Button(
                    "❌ 清空",
                    elem_classes=["gradio-button"]
                )
        
        # 隐藏的数据存储
        video_data_storage = gr.Textbox(visible=False)
        
        # 事件绑定
        analyze_btn.click(
            fn=analyze_video_url,
            inputs=[url_input],
            outputs=[
                download_path_display,
                cookies_status_display,
                video_info_display,
                video_selection,
                video_data_storage,
                video_selection  # 更新选中状态（默认全选）
            ]
        )
        
        download_btn.click(
            fn=download_selected_videos,
            inputs=[
                url_input,
                video_data_storage,
                video_selection,
                auto_extract,
                audio_format,
                keep_original
            ],
            outputs=[download_status]
        )
        
        # 全选按钮事件
        select_all_btn.click(
            fn=select_all_videos,
            inputs=[video_selection],
            outputs=[video_selection]
        )
        
        # 清空按钮事件
        clear_all_btn.click(
            fn=clear_all_selections,
            inputs=[],
            outputs=[video_selection]
        )
    
    return demo


def check_environment():
    """检查运行环境"""
    print("🔧 环境检查...")
    
    # 检查Python解释器
    python_exe = get_python_executable()
    print(f"🐍 Python解释器: {python_exe}")
    
    # 检查yt-dlp
    try:
        result = subprocess.run([python_exe, "-m", "yt_dlp", "--version"], capture_output=True, text=True, check=True)
        print(f"✅ yt-dlp版本: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ yt-dlp不可用: {e}")
        return False
    
    # 检查配置文件
    download_path = get_download_path()
    print(f"📁 下载路径: {download_path}")
    
    # 检查cookies
    cookies_status = check_cookies_status()
    print(f"🍪 {cookies_status}")
    
    return True


if __name__ == "__main__":
    print("🚀 启动视频下载Web界面...")
    
    # 环境检查
    if not check_environment():
        print("❌ 环境检查失败，请检查依赖")
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
