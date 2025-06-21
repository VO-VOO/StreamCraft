"""
视频标题获取模块
支持 B站、YouTube 和其他网站的视频标题获取
"""

import httpx
import re
import json
import subprocess
import os
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs


class VideoTitleFetcher:
    def __init__(self, cookies_path: Optional[str] = None):
        self.cookies_path = cookies_path
        self.session = httpx.Client(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        self._load_cookies()
    def _load_cookies(self):
        """加载 cookies 文件"""
        if self.cookies_path and os.path.exists(self.cookies_path):
            try:
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    # 解析 Netscape cookie 格式
                    cookies_dict = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('\t')
                            if len(parts) >= 7:
                                domain = parts[0]
                                name = parts[5]
                                value = parts[6]
                                if 'bilibili' in domain or 'youtube' in domain:
                                    cookies_dict[name] = value
                    
                    if cookies_dict:
                        # 设置 cookies 到 session
                        for name, value in cookies_dict.items():
                            self.session.cookies.set(name, value)
                        # 减少输出信息
                        pass
            except Exception:
                # 减少错误输出
                pass
    def detect_platform(self, url: str) -> str:
        """检测视频平台"""
        if 'bilibili.com' in url or 'b23.tv' in url:
            return 'bilibili'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        else:
            return 'other'
    
    def get_bilibili_video_info(self, url: str) -> Optional[Dict]:
        """获取B站视频信息"""
        try:
            # 提取 BV 号
            bv_match = re.search(r'BV([a-zA-Z0-9]+)', url)
            if not bv_match:
                return None
            
            bvid = f"BV{bv_match.group(1)}"
            
            # 调用B站API
            api_url = "https://api.bilibili.com/x/web-interface/view"
            params = {'bvid': bvid}
            
            response = self.session.get(api_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    video_data = data.get('data')
                    return video_data
        except Exception:
            pass
        
        return None
    
    def get_youtube_video_info(self, url: str) -> Optional[Dict]:
        """获取YouTube视频信息"""
        try:
            print(f"🔍 正在获取YouTube视频信息: {url}")
            # 提取视频ID或播放列表ID
            if 'youtube.com' in url:
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                
                # 检查是否为播放列表URL
                if 'list' in query_params:
                    list_id = query_params['list'][0]
                    print(f"📋 检测到播放列表ID: {list_id}")
                    
                    # 如果同时有视频ID和播放列表ID，优先获取单个视频信息
                    if 'v' in query_params:
                        video_id = query_params['v'][0]
                        print(f"🎬 检测到视频ID: {video_id}")
                        # 获取单个视频信息
                        video_info = self._parse_youtube_page(url)
                        if video_info:
                            # 添加播放列表ID信息
                            video_info['playlist_id'] = list_id
                            return video_info
                    
                    # 如果没有视频ID或获取视频信息失败，获取播放列表信息
                    return self._get_youtube_playlist_info(list_id)
                
                # 单个视频URL
                elif 'v' in query_params:
                    video_id = query_params['v'][0]
                    print(f"🎬 检测到视频ID: {video_id}")
                else:
                    print("❌ 无法从YouTube URL中提取视频ID或播放列表ID")
                    return None
                    
            elif 'youtu.be' in url:
                # 短链接格式
                video_id = url.split('/')[-1].split('?')[0]
                print(f"🎬 从短链接中检测到视频ID: {video_id}")
            else:
                print("❌ 无效的YouTube URL格式")
                return None
            
            # 使用网页解析方式获取视频信息
            return self._parse_youtube_page(url)
            
        except Exception as e:
            print(f"❌ YouTube信息获取失败: {e}")
        
        return None
    
    def _get_youtube_playlist_info(self, list_id: str) -> Optional[Dict]:
        """获取YouTube播放列表信息"""
        try:
            print(f"🔍 获取YouTube播放列表信息，ID: {list_id}")
            
            # 构建播放列表URL
            playlist_url = f"https://www.youtube.com/playlist?list={list_id}"
            
            # 请求播放列表页面
            response = self.session.get(playlist_url)
            if response.status_code != 200:
                print(f"❌ 请求播放列表页面失败: {response.status_code}")
                return None
            
            content = response.text
            
            # 使用正则表达式获取播放列表标题
            playlist_title_match = re.search(r'"playlistTitle":"([^"]+)"', content) or \
                                 re.search(r'<title>([^<]+)</title>', content)
            
            if playlist_title_match:
                playlist_title = playlist_title_match.group(1).replace(' - YouTube', '')
                
                print(f"✅ 成功获取播放列表标题: {playlist_title}")
                return {
                    'title': playlist_title,
                    'id': list_id,
                }
            else:
                print("❌ 无法解析播放列表标题")
            
        except Exception as e:
            print(f"❌ 获取YouTube播放列表信息失败: {e}")
            
        # 如果失败，尝试使用备选方法 - yt-dlp获取播放列表信息
        try:
            print("🔄 使用yt-dlp获取播放列表信息...")
            cmd = ["yt-dlp", "--get-title", "--playlist-items", "1", f"https://www.youtube.com/playlist?list={list_id}"]
            
            if self.cookies_path and os.path.exists(self.cookies_path):
                cmd.extend(["--cookies", self.cookies_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                playlist_title = result.stdout.strip()
                print(f"✅ yt-dlp成功获取播放列表标题: {playlist_title}")
                return {
                    'title': playlist_title,
                    'id': list_id,
                }
        except Exception as e:
            print(f"❌ yt-dlp获取播放列表信息失败: {e}")
        
        return None
    
    def _parse_youtube_page(self, url: str) -> Optional[Dict]:
        """解析YouTube页面获取视频信息"""
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                content = response.text
                
                # 提取页面标题
                title_match = re.search(r'<title>([^<]+)</title>', content)
                if title_match:
                    title = title_match.group(1).replace(' - YouTube', '')
                    return {'title': title}
            
        except Exception as e:
            print(f"❌ YouTube页面解析失败: {e}")
        
        return None
    
    def get_titles_via_ytdlp(self, videos: List[Dict], max_videos: int = 10) -> List[Dict]:
        """使用 yt-dlp 获取视频标题（备用方案）"""
        print(f"正在通过 yt-dlp 获取前 {min(max_videos, len(videos))} 个视频的真实标题...")
        
        for i, video in enumerate(videos[:max_videos]):
            try:
                print(f"获取第 {i+1} 个视频标题...")
                cmd = ["yt-dlp", "--get-title"]
                if self.cookies_path and os.path.exists(self.cookies_path):
                    cmd.extend(["--cookies", self.cookies_path])
                cmd.append(video['url'])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    real_title = result.stdout.strip()
                    video['title'] = real_title
                    print(f"✓ 获取成功: {real_title}")
                else:
                    print(f"✗ 获取失败，保持原标题: {video['title']}")
            except subprocess.TimeoutExpired:
                print(f"✗ 获取超时，保持原标题: {video['title']}")
            except Exception as e:
                print(f"✗ 获取出错: {e}，保持原标题: {video['title']}")
        
        if len(videos) > max_videos:
            print(f"注意：只获取了前 {max_videos} 个视频的真实标题，其余视频将在下载时显示真实标题")
        
        return videos
    def enhance_videos(self, videos: List[Dict], url: str) -> List[Dict]:
        """
        增强视频标题信息（主方法）
        """
        if not videos:
            return videos
        
        platform = self.detect_platform(url)
        
        # 根据平台类型选择对应的标题获取方法
        if platform == 'bilibili':
            return self._enhance_bilibili_titles(videos, url)
        elif platform == 'youtube':
            return self._enhance_youtube_titles(videos, url)
        else:
            # 根据视频数量选择备选方案
            if len(videos) <= 10:
                return self.get_titles_via_ytdlp(videos, max_videos=len(videos))
            else:
                return self._use_fallback_titles(videos)
    def _enhance_bilibili_titles(self, videos: List[Dict], url: str) -> List[Dict]:
        """增强B站视频标题"""
        
        video_info = self.get_bilibili_video_info(url)
        if video_info:
            pages = video_info.get('pages', [])
            main_title = video_info.get('title', '')
            
            # 匹配分P信息
            for i, video in enumerate(videos):
                playlist_index = video.get('playlist_index', i + 1)
                
                # 在pages中查找对应的分P
                matching_page = None
                for page in pages:
                    if page.get('page') == playlist_index:
                        matching_page = page
                        break
                
                if matching_page:
                    part_title = matching_page.get('part', f'P{playlist_index}')
                    video['title'] = f"{main_title} - {part_title}"
                    # 添加时长信息
                    if 'duration' in matching_page:
                        duration = matching_page['duration']
                        minutes = duration // 60
                        seconds = duration % 60
                        video['duration'] = f"{minutes:02d}:{seconds:02d}"
                else:
                    video['title'] = f"{main_title} - P{playlist_index}"
            
            return videos
        else:
            return self._use_fallback_titles(videos)
    
    def _enhance_youtube_titles(self, videos: List[Dict], url: str) -> List[Dict]:
        """增强YouTube视频标题"""
        print("🔄 正在获取YouTube视频标题...")
        
        # 检查是否为播放列表
        if 'list=' in url:
            print("📋 检测到YouTube播放列表")
            
            # 获取播放列表信息
            parsed = urlparse(url)
            list_id = parse_qs(parsed.query).get('list', [None])[0]
            
            if list_id:
                print(f"📋 播放列表ID: {list_id}")
                video_info = self._get_youtube_playlist_info(list_id)
                
                if video_info:
                    # 使用播放列表信息处理标题
                    playlist_title = video_info.get('title', '')
                    print(f"📋 播放列表标题: {playlist_title}")
                    
                    for i, video in enumerate(videos):
                        playlist_index = video.get('playlist_index', i + 1)
                        video['title'] = f"{playlist_title} - {playlist_index}"
                    
                    return videos
        
        # 获取单个视频信息
        video_info = self.get_youtube_video_info(url)
        if video_info:
            print("🎬 获取到YouTube视频信息")
            main_title = video_info.get('title', '')
            
            if len(videos) == 1:
                # 单个视频情况
                videos[0]['title'] = main_title
            else:
                # 多个视频但不是播放列表的情况
                for i, video in enumerate(videos):
                    playlist_index = video.get('playlist_index', i + 1)
                    video['title'] = f"{main_title} - Part {playlist_index}"
            
            return videos
          # 如果前面的方法都失败，尝试使用yt-dlp
        print("⚠️ 使用yt-dlp备选方案获取YouTube视频标题")
        if len(videos) <= 10:
            return self.get_titles_via_ytdlp(videos, max_videos=len(videos))
        else:
            return self._use_fallback_titles(videos)
      # _enhance_other_titles方法已被移除
    # 处理逻辑已合并到主方法enhance_videos中
    
    def _use_fallback_titles(self, videos: List[Dict]) -> List[Dict]:
        """使用回退标题方案（合集标题+索引）"""
        print("⚠️ 使用回退标题方案")
        for video in videos:
            if not video.get('title') or video['title'].startswith('视频_'):
                playlist_title = video.get('playlist_title', '')
                playlist_index = video.get('playlist_index', 1)
                
                if playlist_title:
                    video['title'] = f"{playlist_title} - P{playlist_index}"
                else:
                    video['title'] = f"视频_{playlist_index}"
        
        return videos
    
    def close(self):
        """关闭会话"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def enhance_video_titles(videos: List[Dict], url: str, cookies_path: Optional[str] = None) -> List[Dict]:
    """
    便捷函数：增强视频标题信息
    
    Args:
        videos: 视频列表
        url: 原始URL
        cookies_path: cookies文件路径
    
    Returns:
        增强后的视频列表
    """
    with VideoTitleFetcher(cookies_path) as fetcher:
        return fetcher.enhance_videos(videos, url)


if __name__ == "__main__":
    # 示例用法
    test_videos = [
        {'title': '视频_1', 'url': 'https://www.bilibili.com/video/BV1xxxxxx', 'playlist_index': 1, 'playlist_title': '测试合集'},
        {'title': '视频_2', 'url': 'https://www.bilibili.com/video/BV2xxxxxx', 'playlist_index': 2, 'playlist_title': '测试合集'}
    ]
    test_url = "https://www.bilibili.com/video/BV1xxxxxx"
    
    enhanced_videos = enhance_video_titles(test_videos, test_url, cookies_path='cookies.txt')
    
    print("增强后的视频标题:")
    for video in enhanced_videos:
        print(video['title'])


