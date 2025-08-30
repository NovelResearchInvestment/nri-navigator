# NRI Navigator 工具集

NRI Navigator 是一个基于Hugo的静态响应式网址导航项目，包含完整的网站管理工具集。

## 🎯 项目概述

本项目基于 [WebStack-Hugo](https://github.com/shenweiyan/WebStack-Hugo) 主题开发，是一个基于Hugo的静态响应式网址导航主题，提供了一套完整的网址导航管理解决方案，包括：

- 🌐 **静态导航网站**: 基于Hugo的响应式网址导航
- 🔧 **管理工具集**: Logo获取、链接检查、描述生成等自动化工具
- 📊 **监控报告**: 全面的网站状态监控和报告系统

### 主题特色功能

这是 Hugo 版 WebStack 主题，可以借助以下平台直接托管部署，无需服务器：

- [Webify](https://webify.cloudbase.net/) | [Netlify](https://app.netlify.com/) | [Cloudflare Pages](https://pages.cloudflare.com) | [Vercel](https://vercel.com) | [Github Pages](https://pages.github.com/)

总体特点：

- 采用了高效的 Hugo 部署方式，方便快速
- 主要配置信息集成到 `config.toml`，一键完成各种自定义配置
- 导航信息集中在 `data/webstack.yml` 文件中，方便后续增删改动
- 手机电脑自适应以及夜间模式支持
- 集成搜索功能，以及下拉的热词选项（基于百度 API）
- 集成一言、和风天气的 API

## 🚀 快速开始

### 环境要求

- Hugo v0.68.3+
- Python 3.7+
- Git

### 安装依赖

```bash
# Hugo安装 (Ubuntu/Debian)
sudo apt-get install hugo

# Python依赖
pip install requests pyyaml beautifulsoup4

# 可选：剪贴板功能支持
sudo apt-get install xclip
```

### 启动开发服务器

```bash
# 克隆项目
git clone <repository-url>
cd nri-navigator

# 启动Hugo开发服务器
hugo server --buildDrafts --buildFuture

# 访问 http://localhost:1313
```

## 🔧 管理工具

项目包含三个核心管理工具，所有工具生成的文件都保存在 `scripts/results/` 目录下。

### 1. Logo获取工具 (logo_tool.py)

自动获取和管理网站Logo，支持多API源和质量评估。

#### 功能特点

- 🎯 **智能获取**: 多API源自动切换，提高成功率
- 🇨🇳 **中国优化**: 针对中国网站的特殊优化策略
- 📊 **质量评估**: Logo质量检查和最佳选择算法
- 🔄 **批量处理**: 支持并行处理，提高效率
- ✅ **验证检查**: 智能验证现有logo的有效性

#### 使用方法

```bash
# 普通获取单个网站logo
python3 scripts/logo_tool.py get example.com

# 高质量获取（推荐）- 评估多个源，选择最佳质量
python3 scripts/logo_tool.py get-hq example.com

# 检查logo质量
python3 scripts/logo_tool.py check "https://example.com/favicon.ico"

# 扫描缺失logo的网站
python3 scripts/logo_tool.py scan

# 批量更新缺失的logo
python3 scripts/logo_tool.py update

# 验证现有logo有效性
python3 scripts/logo_tool.py verify

# 生成详细状态报告
python3 scripts/logo_tool.py report
```

#### 中国网站优化

- 📡 使用DNSPod、iowen等中国本土API服务
- ⏱️ 延长超时时间适应网络环境
- 🔄 API失败时尝试直接访问网站获取favicon
- 🎯 智能识别中国域名后缀

#### 质量评估系统

`get-hq`命令使用智能质量评估算法：

- **文件大小**: 1KB-20KB为最佳范围（+50分）
- **API优先级**: 排名靠前的API获得更高分数
- **专业服务**: FaviconKit、Icon.Horse等专业服务加分（+20分）
- **大尺寸**: 明确支持大尺寸的API加分（+15分）

### 2. 链接检查工具 (link_checker.py)

检查导航中所有链接的可用性和响应状态。

#### 功能特点

- 🔗 **全面检查**: HTTP状态码、响应时间、重定向跟踪
- 🚀 **并行处理**: 多线程提高检查效率
- 📊 **多种格式**: Markdown、JSON、纯文本报告
- 🎯 **灵活过滤**: 按分类、状态、响应时间过滤
- ⚡ **快速模式**: 仅检查连通性，跳过详细分析

#### 使用方法

```bash
# 检查所有链接（默认Markdown格式）
python3 scripts/link_checker.py

# 快速检查模式
python3 scripts/link_checker.py --quick

# 限制检查数量
python3 scripts/link_checker.py --limit 50

# 指定输出格式
python3 scripts/link_checker.py --format json
python3 scripts/link_checker.py --format text

# 检查单个URL
python3 scripts/link_checker.py --url https://example.com

# 静默模式（仅输出到文件）
python3 scripts/link_checker.py --quiet

# 自定义线程数
python3 scripts/link_checker.py --threads 10
```

#### 检查指标

- **HTTP状态码**: 200, 404, 500等状态分析
- **响应时间**: 毫秒级响应时间测量
- **重定向**: 自动跟踪和记录重定向链
- **SSL证书**: HTTPS网站证书有效性检查
- **可用性**: 总体连接可用性评估

### 3. 描述生成工具 (description_generator.py)

自动获取网站信息并生成描述文本。

#### 功能特点

- 🤖 **智能提取**: 自动从网页标题、meta描述提取信息
- 🎯 **批量处理**: 支持批量生成缺失的描述
- 🔄 **增量更新**: 只处理缺失描述的网站
- 🌐 **编码适配**: 支持多种字符编码自动检测
- ⚡ **请求优化**: 智能请求头和超时处理

#### 使用方法

```bash
# 获取单个网站描述
python3 scripts/description_generator.py get https://example.com

# 扫描缺失描述的网站
python3 scripts/description_generator.py scan

# 批量更新缺失描述（预览）
python3 scripts/description_generator.py update --dry-run

# 实际执行批量更新
python3 scripts/description_generator.py update

# 限制处理数量
python3 scripts/description_generator.py update --limit 10

# 使用自定义webstack文件
python3 scripts/description_generator.py scan --webstack /path/to/webstack.yml
```

#### 提取策略

1. **标题提取**: 优先使用`<title>`标签内容
2. **Meta描述**: 提取`meta name="description"`内容
3. **智能清理**: 去除常见的网站后缀和无关信息
4. **长度控制**: 自动截断过长描述，保持合适长度
5. **编码处理**: 自动检测和转换字符编码

## 🧪 测试套件

项目包含完整的测试套件，位于 `scripts/tests/` 目录。

### 运行测试

```bash
# 运行所有工具测试
python3 scripts/tests/run_all_tests.py

# 单独测试各工具
python3 scripts/tests/test_logo_tool.py
python3 scripts/tests/test_link_checker.py
python3 scripts/tests/test_description_generator.py
```

### 测试覆盖

- ✅ **功能测试**: 各命令的基本功能验证
- ✅ **输出测试**: 文件输出格式和位置验证
- ✅ **错误处理**: 异常情况和错误输入处理
- ✅ **性能测试**: 并发处理和超时控制

## 📁 项目结构

```
nri-navigator/
├── config.toml              # Hugo配置文件
├── data/
│   └── webstack.yml         # 导航数据配置
├── content/
│   └── about.md            # 关于页面
├── layouts/                 # 自定义布局
├── themes/
│   └── WebStack-Hugo/      # 主题文件
└── scripts/                # 管理工具
    ├── logo_tool.py        # Logo获取工具
    ├── link_checker.py     # 链接检查工具
    ├── description_generator.py  # 描述生成工具
    ├── results/            # 工具输出文件
    ├── tests/              # 测试脚本
    └── README.md           # 工具文档
```

## 🔄 完整工作流程

### 新项目建立流程

```bash
# 1. 启动开发服务器
hugo server --buildDrafts --buildFuture

# 2. 扫描当前状态
python3 scripts/logo_tool.py scan
python3 scripts/link_checker.py --quick
python3 scripts/description_generator.py scan

# 3. 批量更新（预览）
python3 scripts/logo_tool.py update --dry-run
python3 scripts/description_generator.py update --dry-run

# 4. 执行更新
python3 scripts/logo_tool.py update
python3 scripts/description_generator.py update

# 5. 验证和生成报告
python3 scripts/logo_tool.py verify
python3 scripts/link_checker.py
python3 scripts/logo_tool.py report
```

### 日常维护流程

```bash
# 1. 检查链接状态
python3 scripts/link_checker.py --quick

# 2. 验证logo有效性
python3 scripts/logo_tool.py verify

# 3. 更新问题项目
python3 scripts/logo_tool.py update
python3 scripts/description_generator.py update --limit 5

# 4. 生成状态报告
python3 scripts/logo_tool.py report
```

## 📊 性能数据

基于实际测试的性能指标：

### Logo获取工具
- **整体成功率**: 98.4% (125/127)
- **中国网站优化**: 提升52.4% (44.3% → 96.7%)
- **平均响应时间**: 2.3秒/网站
- **并发处理**: 支持最多5个线程

### 链接检查工具
- **检查速度**: 平均1.2秒/链接
- **并发能力**: 支持最多20个线程
- **准确率**: 99.5%以上
- **超时控制**: 智能超时和重试机制

### 描述生成工具
- **提取成功率**: 85-90%
- **平均处理时间**: 3.5秒/网站
- **内容质量**: 自动去重和清理
- **编码支持**: 支持UTF-8/GBK/GB2312等

## ⚙️ 配置说明

### Hugo配置 (config.toml)

```toml
baseURL = "https://your-domain.com"
languageCode = "zh-cn"
title = "NRI Navigator"
theme = "WebStack-Hugo"

[params]
  # 自定义配置参数
  description = "NRI团队导航"
  keywords = ["导航", "工具", "研究"]
```

### 导航数据 (data/webstack.yml)

```yaml
# 分类配置
- taxonomy: 工具分类
  icon: fas fa-tools fa-lg
  list:
    - term: 子分类
      links:
        - title: 网站名称
          logo: https://example.com/logo.png
          url: https://example.com
          description: 网站描述
```

### 工具配置

各工具支持以下通用参数：

- `--webstack`: 指定webstack.yml文件路径
- `--dry-run`: 预览模式，不实际修改文件
- `--threads`: 并行处理线程数
- `--limit`: 限制处理数量
- `--quiet`: 静默模式

## 🚨 故障排除

### 常见问题

1. **Hugo服务启动失败**
   ```bash
   # 检查Hugo版本
   hugo version
   # 确保版本 >= 0.68.3
   ```

2. **工具权限问题**
   ```bash
   # 给脚本添加执行权限
   chmod +x scripts/*.py
   ```

3. **依赖包缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

4. **网络连接问题**
   - 中国网站建议在国内网络环境下使用
   - 可能需要调整超时时间和重试次数
   - 部分API可能有访问限制

### 性能优化建议

- **中国网站**: 使用2个线程效果最佳
- **国际网站**: 可以使用3-5个线程
- **大批量处理**: 建议分批处理，避免API限制
- **内存优化**: 超大数据集可考虑增加系统内存

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 运行测试套件
5. 提交Pull Request

### 代码规范

- Python代码遵循PEP 8规范
- 添加适当的注释和文档字符串
- 新功能需要包含对应的测试用例

## 📄 许可证

本项目基于原始WebStack主题开发，遵循相应的开源许可证。

## 🔗 相关链接

- [Hugo官方文档](https://gohugo.io/documentation/)
- [WebStack原项目](https://github.com/WebStackPage/WebStackPage.github.io)
- [WebStack-Hugo主题](https://github.com/shenweiyan/WebStack-Hugo)

## 🙏 致谢

本项目的部分代码参考了以下几个开源项目，特此感谢：

- [WebStackPage/WebStackPage.github.io](https://github.com/WebStackPage/WebStackPage.github.io)
- [liutongxu/liutongxu.github.io](https://github.com/liutongxu/liutongxu.github.io)
- [iplaycode/webstack-hugo](https://github.com/iplaycode/webstack-hugo)

感谢以下朋友对原主题所做出的贡献：
- [@yuanj82](https://github.com/yuanj82)        
- [@yanbeiyinhanghang](https://github.com/yinhanghang)     
- [@jetsung](https://github.com/jetsung)

## 📈 更新日志

### v1.1 (当前版本)
- ➕ 新增高质量logo获取功能
- ➕ 新增logo质量检查和评估
- ➕ 报告中添加时间戳信息
- 🔧 升级API参数，支持128px大尺寸logo
- 📊 改进质量评估算法
- 🧪 添加完整测试套件
- 📁 统一输出文件到results目录

### v1.0
- 🎉 统一多个logo获取脚本
- 🇨🇳 实现中国网站优化策略
- ✅ 添加logo验证和清理功能
- 📈 支持详细状态报告生成
- 🔄 实现批量并行处理
- 📋 集成剪贴板功能
- 🔗 添加链接检查工具
- 📝 添加描述生成工具
