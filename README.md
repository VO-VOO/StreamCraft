# 🎬 视频下载与音频提取工具

一个功能强大的视频下载和音频提取工具，提供美观的 Web 界面。支持从各种视频网站下载视频并提取音频，具有深色主题的现代化用户界面。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 主要功能

### 🎥 视频下载器

- **智能识别**: 自动检测单个视频或视频合集
- **多选下载**: 从视频合集中选择指定视频进行下载
- **认证支持**: 支持 cookies.txt 文件进行身份验证
- **自动命名**: 创建时间戳文件夹，避免文件冲突
- **进度显示**: 实时显示下载进度和状态

### 🎵 音频提取器

- **批量处理**: 支持单个文件或文件夹批量处理
- **多种格式**: 支持输出高品质 AAC 或无损 FLAC 格式
- **视频格式支持**: 兼容 MP4、AVI、MKV、MOV、WMV 等 11 种常见视频格式
- **文件管理**: 可选择保留或删除原视频文件
- **安全处理**: 使用临时文件机制，确保源文件安全

### 🌐 Web 界面

- **深色主题**: 现代化深色界面，护眼舒适
- **响应式设计**: 适配不同屏幕尺寸
- **实时反馈**: 详细的操作状态和进度显示
- **直观操作**: 简洁明了的用户交互界面

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **uv**: Python 包管理器
- **FFmpeg**: 音频视频处理工具
- **yt-dlp**: 视频下载工具

### 安装依赖

#### 1. 安装系统依赖

**Windows:**

```bash
# 安装FFmpeg (使用Chocolatey)
choco install ffmpeg

# 或者下载FFmpeg并添加到PATH环境变量
# https://ffmpeg.org/download.html
```

**macOS:**

```bash
# 使用Homebrew安装
brew install ffmpeg yt-dlp
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install ffmpeg
pip install yt-dlp
```

#### 2. 设置 Python 环境

```bash
# 进入项目目录
cd Video_download

# 使用uv创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate

# 安装项目依赖
uv pip install -r requirements.txt
```

### 运行应用

```bash
# 启动Web界面
python gradio_app.py

# 或者使用命令行版本
python main.py  # 主菜单
python 音频提取器.py  # 直接使用音频提取器
python dlp下载器.py  # 直接使用视频下载器
```

Web 界面默认在 `http://localhost:7860` 启动

## 📝 使用说明

### 视频下载

1. **输入 URL**: 在输入框中粘贴视频网址
2. **分析视频**: 点击"分析 URL"按钮
3. **选择视频**: 如果是合集，勾选要下载的视频
4. **设置选项**:
   - 选择是否自动提取音频
   - 选择音频格式（AAC/FLAC）
   - 选择是否保留原视频
5. **开始下载**: 点击"开始下载"按钮

### 音频提取

1. **选择路径**: 输入视频文件或文件夹路径
2. **扫描文件**: 查看找到的视频文件列表
3. **选择文件**: 勾选要处理的视频文件
4. **设置格式**: 选择输出音频格式
5. **开始提取**: 点击"开始提取"按钮

### Cookies 设置

对于需要登录的网站，请：

1. 使用浏览器扩展导出 cookies.txt 文件
2. 将 cookies.txt 放置在项目根目录
3. 界面会自动检测并显示 cookies 状态

## 📁 项目结构

```
Video_download/
├── gradio_app.py          # Web界面主程序
├── main.py               # 命令行主菜单
├── 音频提取器.py          # 音频提取功能
├── dlp下载器.py          # 视频下载功能
├── cookies.txt           # 网站认证文件
├── README.md             # 项目说明
├── pyproject.toml        # 项目配置
├── uv.lock              # 依赖锁定文件
└── .venv/               # 虚拟环境
```

## 🔧 技术栈

- **后端**: Python 3.8+
- **Web 框架**: Gradio 4.0+
- **视频处理**: FFmpeg
- **视频下载**: yt-dlp
- **包管理**: uv
- **界面**: HTML/CSS/JavaScript (Gradio)

## 📋 支持的网站

支持 yt-dlp 兼容的所有网站，包括但不限于：

- YouTube
- Bilibili
- Twitter
- Instagram
- TikTok
- 等 500+个网站

## ⚙️ 配置选项

### 下载设置

- **下载目录**: 默认为 `C:\Users\chenw\Videos\下载_时间戳/`
- **文件命名**: 使用视频标题自动命名
- **并发下载**: 支持多线程下载加速

### 音频设置

- **AAC 格式**: 320k 高品质，兼容性好
- **FLAC 格式**: 无损音质，文件较大
- **超时设置**: 单个文件处理超时 5 分钟

## 🐛 故障排除

### 常见问题

**1. FFmpeg 未找到**

```bash
# 确保FFmpeg已安装并添加到PATH
ffmpeg -version
```

**2. yt-dlp 下载失败**

```bash
# 更新yt-dlp到最新版本
pip install --upgrade yt-dlp
```

**3. 权限错误**

- 确保对下载目录有写入权限
- 以管理员身份运行程序

**4. 编码问题**

- 确保系统支持 UTF-8 编码
- 检查文件名是否包含特殊字符

### 日志查看

程序运行时会在控制台显示详细日志，包括：

- 下载进度
- 转换状态
- 错误信息
- 文件保存位置

## 🤝 贡献指南

欢迎提交 Bug 报告、功能请求或代码贡献！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理框架
- [Gradio](https://gradio.app/) - 机器学习 Web 界面框架

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 🐛 [提交 Issue](../../issues)
- 💬 [讨论区](../../discussions)

---

⭐ 如果这个项目对你有帮助，请给一个 Star 支持！
