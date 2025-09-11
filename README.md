# Azure Front Door 缓存清除工具

这是一个简单高效的 Python 工具集，用于清除 Azure Global Front Door 的缓存，并验证缓存刷新效果。专为运维团队设计，可与现有运维平台集成，提供便捷的缓存管理体验。

## 🚀 功能特性

- 🔐 **安全认证**: 使用 Azure 服务主体进行安全认证
- ⚡ **并行处理**: 多个 endpoints 并行清除，5-10倍速度提升  
- 🎯 **交互式选择**: 支持清除所有或选择特定的 endpoints
- 📋 **智能发现**: 自动列出可用的 endpoints
- 🔍 **验证工具**: 内置缓存刷新验证功能
- ⚙️ **灵活配置**: 通过环境变量进行配置
- 📝 **详细日志**: 完整的操作日志和错误处理
- � **向后兼容**: 保持 API 稳定性

## 📦 项目组成

### 核心程序
- **`purge_cache.py`** - 主程序：缓存清除工具
- **`verify_cache_refresh.py`** - 验证工具：检测缓存刷新效果

### 配置文件
- **`requirements.txt`** - Python 依赖包
- **`.env.example`** - 配置模板
- **`run.sh`** - 一键启动脚本

## ⚡ 快速开始

### 1. 环境准备

```bash
# 克隆项目到本地
git clone https://github.com/teo-ma/azure-frontdoor-cache-purge.git
cd azure-frontdoor-cache-purge

# 使用一键启动脚本（推荐）
chmod +x run.sh
./run.sh
```

首次运行时，脚本会自动：
- 创建 Python 虚拟环境
- 安装必要的依赖包
- 复制配置文件模板
- 提示填入 Azure 配置信息

### 2. 配置 Azure 认证

编辑 `.env` 文件，填入您的 Azure 配置：

```env
# Azure 服务主体认证信息
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Azure Front Door 配置
AZURE_SUBSCRIPTION_ID=your-subscription-id
RESOURCE_GROUP_NAME=your-resource-group-name
FRONT_DOOR_NAME=your-front-door-name

# 要清除的缓存路径（可选，默认清除所有）
PURGE_PATHS=/*, /api/*, /images/*
```

### 3. 获取 Azure 服务主体

使用 Azure CLI 创建服务主体：
```bash
az login
az ad sp create-for-rbac --name "front-door-purge-sp" \
  --role "CDN Profile Contributor" \
  --scopes /subscriptions/{your-subscription-id}
```

### 4. 运行程序

```bash
# 方式1: 使用启动脚本（推荐）
./run.sh

# 方式2: 直接运行（需要先激活虚拟环境）
python purge_cache.py
```
## 🎮 使用指南

### 交互式缓存清除

运行程序后，会显示交互式选择界面：

```
🔧 选择操作模式:
1. 清除所有 endpoints 的缓存
2. 选择特定的 endpoints 清除缓存

请选择操作模式 (1 或 2): 
```

**操作选项**：
- **选项1**: 自动并行清除所有可用 endpoints 的缓存
- **选项2**: 从列表中选择要清除缓存的 endpoints（支持多选，如: `1,3,5`）

### 缓存验证工具

清除缓存后，使用验证工具确认效果：

```bash
# 运行验证脚本
python verify_cache_refresh.py
```

验证工具会：
- 🔍 检测响应头中的缓存状态
- ⏱️ 测量响应时间变化  
- 📊 提供详细的验证报告
- 💡 给出优化建议

### 编程集成

将工具集成到您的运维平台：

```python
from purge_cache import AzureFrontDoorPurgeClient

# 初始化客户端
client = AzureFrontDoorPurgeClient()

# 方式1: 并行清除指定 endpoints
endpoints = ["web-endpoint", "api-endpoint", "cdn-endpoint"]
results = client.purge_cache_parallel(endpoints)

# 方式2: 清除所有 endpoints
success = client.purge_cache()

# 方式3: 清除特定 endpoint
client.purge_specific_endpoint("api-endpoint", ["/api/v1/*", "/api/v2/*"])

# 方式4: 列出可用 endpoints
client.list_endpoints()
```

## ⚡ 性能优势

### 并行处理加速

| 场景 | 串行处理 | 并行处理 | 速度提升 |
|------|----------|----------|----------|
| 3个 Endpoints | ~30秒 | ~10秒 | **3倍** |
| 5个 Endpoints | ~50秒 | ~10秒 | **5倍** |
| 10个 Endpoints | ~100秒 | ~20秒 | **5倍** |

### 处理特性
- ⚡ **最多5个并行线程**：避免过度占用资源
- 📊 **实时进度跟踪**：显示 `[1/5]`, `[2/5]`, `[3/5]` 等进度
- 🛡️ **错误隔离**：单个 endpoint 失败不影响其他
- 🔄 **自动重试**：网络异常时自动重试

## ⚙️ 配置选项

### 缓存路径配置

在 `.env` 文件中自定义清除路径：

```env
# 清除所有内容
PURGE_PATHS=/*

# 清除特定路径
PURGE_PATHS=/api/*, /images/*, /css/*, /js/*

# 清除多个API版本
PURGE_PATHS=/api/v1/*, /api/v2/*, /static/*

# 清除特定文件类型
PURGE_PATHS=/*.js, /*.css, /*.png, /*.jpg
```

### 权限要求

确保您的 Azure 服务主体具有以下权限：
- **CDN Profile Contributor** 角色（订阅或资源组级别）
- **访问目标 Front Door 资源**的权限

## 📋 示例输出

### 单 Endpoint 清除
```
Azure Front Door Standard 缓存清除工具
==================================================
正在获取 Front Door 'my-front-door' 的 endpoints...
可用的 endpoints (1 个):
  1. web-endpoint - web.azurefd.net (状态: Succeeded)

🔧 选择操作模式:
1. 清除所有 endpoints 的缓存
2. 选择特定的 endpoints 清除缓存

请选择操作模式 (1 或 2): 1
✅ 已选择清除所有 1 个 endpoints 的缓存

🚀 开始执行缓存清除操作...
📁 清除路径: ['/*', '/api/*', '/images/*']
⏳ 开始清除 endpoint 'web-endpoint' 的缓存...
✅ Endpoint 'web-endpoint' 缓存清除操作已提交并确认
   📋 清除路径: /*, /api/*, /images/*
   ⏰ 完成时间: 2025-09-11 13:23:47

🎉 所有缓存清除操作成功完成!
✅ 成功清除了 1 个 endpoints 的缓存
```

### 多 Endpoint 并行清除
```
Azure Front Door Standard 缓存清除工具
==================================================
可用的 endpoints (3 个):
  1. web-endpoint - web.azurefd.net (状态: Succeeded)  
  2. api-endpoint - api.azurefd.net (状态: Succeeded)
  3. cdn-endpoint - cdn.azurefd.net (状态: Succeeded)

� 选择操作模式:
1. 清除所有 endpoints 的缓存
2. 选择特定的 endpoints 清除缓存

请选择操作模式 (1 或 2): 2

📋 可用的 endpoints (3 个):
  1. web-endpoint - web.azurefd.net (状态: Succeeded)
  2. api-endpoint - api.azurefd.net (状态: Succeeded)  
  3. cdn-endpoint - cdn.azurefd.net (状态: Succeeded)

请选择要清除缓存的 endpoints (输入序号，多个用逗号分隔，如: 1,3,5): 1,2
✅ 已选择 2 个 endpoints: web-endpoint, api-endpoint

🚀 开始并行清除 2 个 endpoints 的缓存...
📁 清除路径: ['/*', '/api/*', '/images/*']
⚡ 最大并行线程数: 5
============================================================
⏳ 开始清除 endpoint 'web-endpoint' 的缓存...
⏳ 开始清除 endpoint 'api-endpoint' 的缓存...
✅ [1/2] Endpoint 'web-endpoint' 缓存清除成功
✅ [2/2] Endpoint 'api-endpoint' 缓存清除成功
============================================================
📊 并行缓存清除完成: 2/2 个 endpoints 成功

🎉 所有缓存清除操作成功完成!
✅ 成功清除了 2 个 endpoints 的缓存
```

## 🔍 缓存验证工具

### 使用验证脚本

清除缓存后，运行验证工具确认效果：

```bash
python verify_cache_refresh.py
```

### 验证功能
- 🔍 **HTTP响应分析**：检查响应头和状态码
- 📊 **缓存状态检测**：分析 `X-Cache`、`Cache-Control` 等头信息
- ⏱️ **响应时间测量**：对比缓存清除前后的响应时间
- 📈 **多次测试**：连续测试以观察缓存恢复过程
- 💡 **智能建议**：根据测试结果提供优化建议

### 手动验证方法

#### 方法一：浏览器验证
```bash
# 1. 强制刷新页面
Ctrl+F5 (Windows) 或 Cmd+Shift+R (Mac)

# 2. 开发者工具验证
F12 → Network 标签页 → 检查响应头中的 X-Cache 字段
- MISS: 缓存已清除
- HIT: 使用缓存
```

#### 方法二：命令行验证
```bash
# 检查响应头
curl -I https://your-site.azurefd.net/

# 查看缓存状态和响应时间
curl -w "Time: %{time_total}s\n" -I https://your-site.azurefd.net/

# 检查特定路径
curl -I https://your-site.azurefd.net/api/health
```

### 验证指标说明

| 指标 | 缓存清除前 | 缓存清除后 | 说明 |
|------|------------|------------|------|
| **X-Cache** | HIT | MISS → HIT | 首次请求为MISS，后续逐渐变为HIT |
| **响应时间** | 快速 | 稍慢 → 恢复 | 第一次请求可能稍慢 |
| **内容版本** | 旧版本 | 新版本 | 显示最新更新的内容 |
| **ETag** | 不变 | 可能改变 | 内容变化时ETag会更新 |

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 认证失败
```
❌ 错误: azure.core.exceptions.ClientAuthenticationError
```
**解决方案**:
- 检查 `.env` 文件中的服务主体配置
- 验证 AZURE_TENANT_ID、AZURE_CLIENT_ID、AZURE_CLIENT_SECRET
- 确认服务主体具有正确的权限

#### 2. 资源未找到
```
❌ 错误: ResourceNotFoundError
```
**解决方案**:
- 验证 AZURE_SUBSCRIPTION_ID 是否正确
- 检查 RESOURCE_GROUP_NAME 和 FRONT_DOOR_NAME 拼写
- 确认资源存在于指定订阅中

#### 3. 权限不足
```
❌ 错误: AuthorizationFailed
```
**解决方案**:
- 为服务主体分配 "CDN Profile Contributor" 角色
- 确认权限作用域包含目标资源组或订阅

#### 4. 条件访问策略阻止
```
❌ 错误: ConditionalAccessPolicy
```
**解决方案**:
- 联系 Azure 管理员调整条件访问策略
- 使用符合策略要求的网络环境运行

#### 5. 网络连接问题
```
❌ 错误: ConnectionError 或超时
```
**解决方案**:
- 检查网络连接是否正常
- 验证防火墙是否阻止 Azure API 访问
- 重试操作（程序支持部分失败重试）

### 调试模式

开启详细日志以获得更多调试信息：

```bash
# 设置调试环境变量
export AZURE_LOG_LEVEL=DEBUG

# 运行程序
python purge_cache.py
```

## 📁 项目结构

```
azure-frontdoor-cache-purge/
├── purge_cache.py              # 🔥 主程序：缓存清除工具
├── verify_cache_refresh.py     # 🔍 验证工具：检测缓存刷新效果
├── requirements.txt            # 📦 Python 依赖包列表
├── .env.example               # 📝 配置模板文件
├── .env                       # ⚙️ 实际配置（需要填写）
├── run.sh                     # 🚀 一键启动脚本
├── README.md                  # 📖 项目说明文档
├── LICENSE                    # 📄 开源许可证
└── VERSION.md                 # 🏷️ 版本信息
```

## 🤝 运维平台集成

### 集成示例

```python
# 运维平台调用示例
import sys
import json
from purge_cache import AzureFrontDoorPurgeClient

def ops_purge_cache(endpoints=None, paths=None):
    """
    运维平台集成接口
    
    Args:
        endpoints: 要清除的 endpoint 列表，None 表示清除所有
        paths: 要清除的路径列表，None 使用默认配置
    
    Returns:
        dict: 操作结果
    """
    try:
        client = AzureFrontDoorPurgeClient()
        
        if endpoints:
            # 清除指定 endpoints
            results = client.purge_cache_parallel(endpoints, paths)
            success_count = sum(1 for success in results.values() if success)
            
            return {
                "success": success_count == len(endpoints),
                "total": len(endpoints),
                "success_count": success_count,
                "details": results
            }
        else:
            # 清除所有 endpoints
            success = client.purge_cache(paths)
            return {
                "success": success,
                "message": "All endpoints purged" if success else "Purge failed"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# API 调用示例
if __name__ == "__main__":
    # 从命令行参数获取配置
    if len(sys.argv) > 1:
        endpoints = sys.argv[1].split(',') if sys.argv[1] != 'all' else None
        result = ops_purge_cache(endpoints)
        print(json.dumps(result, indent=2))
```

### Jenkins/GitLab CI 集成

```yaml
# .gitlab-ci.yml 示例
purge_cache:
  stage: deploy
  script:
    - ./run.sh
  only:
    - main
  environment:
    name: production
```

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🆕 版本历史

- **v2.0.0** - 添加并行处理和交互式选择功能
- **v1.5.0** - 新增缓存验证工具
- **v1.0.0** - 基础缓存清除功能

---

**🎯 专为运维团队设计，简单高效，开箱即用！**
