# 版本信息

## v1.0.0 - 生产版本

### 发布日期
2025年9月11日

### 功能特性
- ✅ Azure Front Door Standard 缓存清除
- ✅ 多 Endpoint 支持（自动清除所有 endpoints）
- ✅ 服务主体认证
- ✅ 环境变量配置
- ✅ 详细的操作日志
- ✅ 错误处理和恢复
- ✅ 一键启动脚本

### 文件清单
- `purge_cache.py` - 主程序
- `requirements.txt` - Python 依赖
- `.env.example` - 配置模板
- `run.sh` - 启动脚本
- `.gitignore` - Git 忽略文件
- `README.md` - 使用说明
- `VERSION.md` - 版本信息

### 测试状态
- ✅ 单 Endpoint 测试通过
- ✅ 多 Endpoint 测试通过
- ✅ 错误处理测试通过
- ✅ 配置验证测试通过
- ✅ 生产环境测试通过

### 系统要求
- Python 3.7+
- Azure 订阅
- CDN Profile Contributor 权限
