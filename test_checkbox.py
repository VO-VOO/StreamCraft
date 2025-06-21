#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Gradio CheckboxGroup测试脚本
专门验证choices和value的同步更新机制
"""

import gradio as gr
import json

def test_checkbox_update():
    """测试CheckboxGroup的更新"""
    
    # 模拟视频数据
    test_choices = [
        "1. 测试视频1 - 第一个测试视频",
        "2. 测试视频2 - 第二个测试视频", 
        "3. 测试视频3 - 第三个测试视频"
    ]
    
    # 自动选择第一个
    auto_selected = test_choices[:1]
    
    print(f"📝 测试数据:")
    print(f"   choices: {test_choices}")
    print(f"   selected: {auto_selected}")
    
    # 返回更新的CheckboxGroup
    return gr.CheckboxGroup(
        choices=test_choices,
        value=auto_selected,
        label="选择要下载的视频",
        interactive=True
    )

def simulate_analyze_url(url):
    """模拟分析URL的过程"""
    print(f"🔍 模拟分析URL: {url}")
    
    if not url.strip():
        return "❌ 请输入URL", gr.CheckboxGroup(choices=[], value=[])
    
    # 模拟不同类型的结果
    if "single" in url.lower():
        # 单个视频
        choices = ["1. 单个测试视频 - 这是一个单独的视频"]
        selected = choices[:1]
        status = "✅ 检测到单个视频"
    elif "playlist" in url.lower():
        # 视频合集
        choices = [
            "1. 合集视频1 - 第一个合集视频",
            "2. 合集视频2 - 第二个合集视频",
            "3. 合集视频3 - 第三个合集视频",
            "4. 合集视频4 - 第四个合集视频",
            "5. 合集视频5 - 第五个合集视频"
        ]
        selected = choices[:1]  # 自动选择第一个
        status = f"✅ 检测到合集，共 {len(choices)} 个视频"
    else:
        # 默认测试数据
        choices = [
            "1. 默认视频1 - 第一个默认视频",
            "2. 默认视频2 - 第二个默认视频"
        ]
        selected = choices[:1]
        status = "✅ 使用默认测试数据"
    
    print(f"📊 返回数据:")
    print(f"   status: {status}")
    print(f"   choices: {choices}")
    print(f"   selected: {selected}")
    
    # 创建更新的CheckboxGroup
    updated_checkbox = gr.CheckboxGroup(
        choices=choices,
        value=selected,
        label="选择要下载的视频",
        interactive=True
    )
    
    return status, updated_checkbox

def create_test_interface():
    """创建测试界面"""
    with gr.Blocks(title="CheckboxGroup 测试") as demo:
        gr.Markdown("# Gradio CheckboxGroup 更新测试")
        
        with gr.Row():
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="输入测试URL",
                    placeholder="输入 'single', 'playlist' 或其他任意文本",
                    value="https://test.com/single"
                )
                
                analyze_btn = gr.Button("🔍 分析", variant="primary")
                
            with gr.Column(scale=1):
                status_display = gr.Textbox(
                    label="分析状态",
                    value="等待分析...",
                    interactive=False
                )
        
        with gr.Row():
            video_selection = gr.CheckboxGroup(
                choices=[],
                value=[],
                label="选择要下载的视频",
                interactive=True
            )
        
        with gr.Row():
            test_btn = gr.Button("🧪 测试更新")
            clear_btn = gr.Button("❌ 清空")
        
        # 事件绑定
        analyze_btn.click(
            fn=simulate_analyze_url,
            inputs=[url_input],
            outputs=[status_display, video_selection]
        )
        
        test_btn.click(
            fn=test_checkbox_update,
            inputs=[],
            outputs=[video_selection]
        )
        
        clear_btn.click(
            fn=lambda: gr.CheckboxGroup(choices=[], value=[]),
            inputs=[],
            outputs=[video_selection]
        )
    
    return demo

def main():
    """主函数"""
    print("🚀 启动CheckboxGroup测试界面...")
    
    demo = create_test_interface()
    
    # 启动界面
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,  # 使用不同的端口避免冲突
        share=False,
        debug=True
    )

if __name__ == "__main__":
    main()
