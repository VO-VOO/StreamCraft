#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio CheckboxGroup 调试脚本
用于详细分析分析阶段的所有中间变量和返回值
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_python_executable():
    """获取虚拟环境的Python路径"""
    venv_python = Path('.venv/Scripts/python.exe')
    if venv_python.exists():
        return str(venv_python.absolute())
    return sys.executable

def check_playlist(url):
    """检查是否为视频合集"""
    print(f"\n🔍 [DEBUG] 开始检查URL: {url}")
    
    python_exe = get_python_executable()
    print(f"🐍 [DEBUG] 使用Python: {python_exe}")
    
    cmd = [
        python_exe, '-m', 'yt_dlp',
        '--flat-playlist',
        '--quiet',
        '--no-warnings',
        '--print', 'id',
        url
    ]
    
    print(f"📝 [DEBUG] 执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )
        
        print(f"🔄 [DEBUG] 命令返回码: {result.returncode}")
        print(f"📤 [DEBUG] stdout: {repr(result.stdout)}")
        print(f"❌ [DEBUG] stderr: {repr(result.stderr)}")
        
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            print(f"📊 [DEBUG] yt-dlp返回了 {len(result.stdout.strip().split())} 行数据")
            print(f"🧹 [DEBUG] 过滤空行后有 {len(lines)} 行有效数据")
            
            if len(lines) > 1:
                print("📋 [DEBUG] 检测到视频合集")
                return True, lines
            else:
                print("📹 [DEBUG] 检测到单个视频")
                return False, lines
        else:
            print(f"❌ [DEBUG] yt-dlp执行失败: {result.stderr}")
            return False, []
            
    except subprocess.TimeoutExpired:
        print("⏰ [DEBUG] yt-dlp超时")
        return False, []
    except Exception as e:
        print(f"💥 [DEBUG] yt-dlp异常: {e}")
        return False, []

def get_playlist_videos(url):
    """获取合集中的所有视频信息"""
    print(f"\n📋 [DEBUG] 获取合集视频信息: {url}")
    
    python_exe = get_python_executable()
    cmd = [
        python_exe, '-m', 'yt_dlp',
        '--flat-playlist',
        '--quiet',
        '--no-warnings',
        '--print', '%(id)s|%(title)s',
        url
    ]
    
    print(f"📝 [DEBUG] 执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        
        print(f"🔄 [DEBUG] 命令返回码: {result.returncode}")
        print(f"📤 [DEBUG] stdout前200字符: {repr(result.stdout[:200])}")
        
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            videos = []
            
            for i, line in enumerate(lines):
                if '|' in line:
                    video_id, title = line.split('|', 1)
                    video_info = {
                        'id': video_id.strip(),
                        'title': title.strip(),
                        'index': i + 1
                    }
                    videos.append(video_info)
                    
                    # 只打印前5个视频的调试信息
                    if i < 5:
                        print(f"🎬 [DEBUG] 视频{i+1}: ID={video_id.strip()}, 标题={title.strip()}")
            
            print(f"📊 [DEBUG] 解析到 {len(videos)} 个视频")
            return videos
        else:
            print(f"❌ [DEBUG] 获取视频信息失败: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"💥 [DEBUG] 获取视频信息异常: {e}")
        return []

def enhance_video_titles(videos, url_base):
    """增强视频标题（从video_title_fetcher.py导入）"""
    print(f"\n✨ [DEBUG] 开始增强视频标题，共 {len(videos)} 个视频")
    
    try:
        from video_title_fetcher import enhance_video_titles as enhance_func
        
        # 准备输入数据
        video_data = []
        for video in videos:
            video_data.append({
                'id': video['id'],
                'title': video['title'],
                'index': video['index']
            })
        
        print(f"📝 [DEBUG] 准备传递给enhance_func的数据（前3个）:")
        for i, v in enumerate(video_data[:3]):
            print(f"   {i+1}: {v}")
        
        # 调用增强函数
        print("🚀 [DEBUG] 调用enhance_video_titles...")
        enhanced_videos = enhance_func(video_data, url_base)
        
        print(f"✅ [DEBUG] enhance_func返回 {len(enhanced_videos) if enhanced_videos else 0} 个视频")
        
        if enhanced_videos:
            print(f"📝 [DEBUG] 增强后的数据（前3个）:")
            for i, v in enumerate(enhanced_videos[:3]):
                print(f"   {i+1}: {v}")
                
        return enhanced_videos or videos
        
    except Exception as e:
        print(f"❌ [DEBUG] 增强标题失败: {e}")
        import traceback
        traceback.print_exc()
        return videos

def format_video_choices(videos):
    """格式化视频选择列表"""
    print(f"\n🎯 [DEBUG] 格式化视频选择列表，共 {len(videos)} 个视频")
    
    choices = []
    for i, video in enumerate(videos):
        choice = f"{i+1}. {video.get('title', 'Unknown Title')} - {video.get('enhanced_title', video.get('title', 'Unknown Title'))}"
        choices.append(choice)
        
        # 只打印前5个的调试信息
        if i < 5:
            print(f"🎬 [DEBUG] Choice {i+1}: {choice}")
    
    print(f"📊 [DEBUG] 格式化完成，共 {len(choices)} 个选择项")
    return choices

def analyze_url_debug(url):
    """调试版本的URL分析函数"""
    print(f"\n🔍 [DEBUG] ===== 开始分析URL =====")
    print(f"🌐 [DEBUG] URL: {url}")
    
    # 步骤1: 检查是否为合集
    print(f"\n📋 [DEBUG] ===== 步骤1: 检查是否为合集 =====")
    is_playlist, video_ids = check_playlist(url)
    
    print(f"📊 [DEBUG] 检查结果: is_playlist={is_playlist}, video_ids数量={len(video_ids)}")
    
    if not video_ids:
        print("❌ [DEBUG] 无法获取视频信息")
        return [], [], "❌ 无法获取视频信息"
    
    # 步骤2: 获取视频详细信息
    print(f"\n📋 [DEBUG] ===== 步骤2: 获取视频详细信息 =====")
    if is_playlist:
        videos = get_playlist_videos(url)
    else:
        # 单个视频的处理
        print("📹 [DEBUG] 处理单个视频")
        videos = [{
            'id': video_ids[0] if video_ids else 'unknown',
            'title': '获取中...',
            'index': 1
        }]
    
    print(f"📊 [DEBUG] 获取到 {len(videos)} 个视频信息")
    
    if not videos:
        print("❌ [DEBUG] 无法获取视频详细信息")
        return [], [], "❌ 无法获取视频详细信息"
    
    # 步骤3: 增强视频标题
    print(f"\n✨ [DEBUG] ===== 步骤3: 增强视频标题 =====")
    enhanced_videos = enhance_video_titles(videos, url)
    
    print(f"📊 [DEBUG] 增强后有 {len(enhanced_videos)} 个视频")
    
    # 步骤4: 格式化选择列表
    print(f"\n🎯 [DEBUG] ===== 步骤4: 格式化选择列表 =====")
    choices = format_video_choices(enhanced_videos)
    
    print(f"📊 [DEBUG] 格式化后有 {len(choices)} 个选择项")
    
    # 步骤5: 准备返回值
    print(f"\n🎯 [DEBUG] ===== 步骤5: 准备返回值 =====")
    
    # 默认选择第一个视频
    default_selected = choices[:1] if choices else []
    
    print(f"📝 [DEBUG] choices类型: {type(choices)}")
    print(f"📝 [DEBUG] choices长度: {len(choices)}")
    print(f"📝 [DEBUG] choices前3项: {choices[:3] if choices else []}")
    
    print(f"📝 [DEBUG] default_selected类型: {type(default_selected)}")
    print(f"📝 [DEBUG] default_selected长度: {len(default_selected)}")
    print(f"📝 [DEBUG] default_selected内容: {default_selected}")
    
    status_info = f"✅ 成功分析到 {len(enhanced_videos)} 个视频"
    print(f"📝 [DEBUG] status_info: {status_info}")
    
    print(f"\n🎯 [DEBUG] ===== 返回值准备完成 =====")
    print(f"📊 [DEBUG] 即将返回: choices={len(choices)}项, selected={len(default_selected)}项, status='{status_info}'")
    
    return choices, default_selected, status_info

def test_gradio_update():
    """测试Gradio组件更新"""
    print(f"\n🧪 [DEBUG] ===== 测试Gradio组件更新 =====")
    
    import gradio as gr
    
    # 模拟分析结果
    test_choices = [
        "1. 测试视频1 - 测试标题1",
        "2. 测试视频2 - 测试标题2",
        "3. 测试视频3 - 测试标题3"
    ]
    test_selected = ["1. 测试视频1 - 测试标题1"]
    
    print(f"📝 [DEBUG] 测试数据:")
    print(f"   choices: {test_choices}")
    print(f"   selected: {test_selected}")
    
    # 创建CheckboxGroup
    print(f"🎛️ [DEBUG] 创建CheckboxGroup组件...")
    checkbox_group = gr.CheckboxGroup(
        choices=[],
        value=[],
        label="选择要下载的视频",
        interactive=True
    )
    
    print(f"📊 [DEBUG] CheckboxGroup初始状态:")
    print(f"   choices: {checkbox_group.choices}")
    print(f"   value: {checkbox_group.value}")
    
    # 尝试更新
    print(f"🔄 [DEBUG] 尝试更新CheckboxGroup...")
    try:
        updated = gr.CheckboxGroup(
            choices=test_choices,
            value=test_selected,
            label="选择要下载的视频",
            interactive=True
        )
        print(f"✅ [DEBUG] 更新成功:")
        print(f"   choices: {updated.choices}")
        print(f"   value: {updated.value}")
        
        return updated
        
    except Exception as e:
        print(f"❌ [DEBUG] 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("🚀 启动Gradio CheckboxGroup调试...")
    
    # 测试URL列表
    test_urls = [
        "https://www.bilibili.com/video/BV1YSjQzZET8?t=204.3",  # 单个视频
        "https://www.bilibili.com/video/BV12ozLYtEv4",  # 大合集
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"🧪 测试 {i}/{len(test_urls)}: {url}")
        print(f"{'='*60}")
        
        # 分析URL
        choices, selected, status = analyze_url_debug(url)
        
        print(f"\n📋 [DEBUG] ===== 最终结果 =====")
        print(f"📊 [DEBUG] choices数量: {len(choices)}")
        print(f"📊 [DEBUG] selected数量: {len(selected)}")
        print(f"📊 [DEBUG] status: {status}")
        
        # 检查数据一致性
        print(f"\n🔍 [DEBUG] ===== 数据一致性检查 =====")
        if selected:
            for sel in selected:
                if sel in choices:
                    print(f"✅ [DEBUG] '{sel}' 在choices中")
                else:
                    print(f"❌ [DEBUG] '{sel}' 不在choices中!")
                    print(f"📝 [DEBUG] choices包含: {choices}")
        
        # 模拟Gradio更新
        print(f"\n🎛️ [DEBUG] ===== 模拟Gradio更新 =====")
        try:
            # 这里模拟Gradio的CheckboxGroup.update()
            if choices and selected:
                # 检查selected中的每一项是否都在choices中
                valid_selected = [s for s in selected if s in choices]
                print(f"📊 [DEBUG] 有效的selected项: {len(valid_selected)}/{len(selected)}")
                
                if len(valid_selected) != len(selected):
                    print(f"⚠️ [DEBUG] 有些selected项不在choices中，已过滤")
                    
        except Exception as e:
            print(f"❌ [DEBUG] 模拟更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 测试Gradio组件
    print(f"\n{'='*60}")
    print(f"🧪 测试Gradio组件更新")
    print(f"{'='*60}")
    test_gradio_update()
    
    print(f"\n🎉 调试完成!")

if __name__ == "__main__":
    main()
