# Azure Front Door Standard 缓存清除工具

这是一个简单的 Python 程序，用于清除 Azure Front Door Standard 的缓存，使用 Azure 服务主体进行身份验证。

## 功能特性

- 🔐 使用 Azure 服务主体进行安全认证
- 🚀 支持清除指定路径的缓存
- 📋 自动列出可用的 endpoints
- 🔄 **支持多 Endpoint 缓存清除** - 自动清除所有 endpoints 或指定 endpoint
- ⚡ **并行处理** - 多个 endpoints 并行清除，大幅提升效率
- 🎯 **交互式选择** - 支持选择清除所有或特定的 endpoints
- ⚙️ 通过环境变量进行配置
- 📝 详细的操作日志和错误处理
- 🔍 内置缓存刷新验证功能

## 快速开始

### 1. 安装和配置

```bash
# 克隆或下载项目到本地
# cd 到项目目录

# 使用启动脚本（推荐）
./run.sh
```

第一次运行时，脚本会：
- 自动创建 Python 虚拟环境
- 安装所需依赖包
- 复制配置文件模板
- 提示您填入 Azure 配置信息

### 2. 配置 Azure 认证信息

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

### 3. 获取 Azure 服务主体信息

使用 Azure CLI：
```bash
az login
az ad sp create-for-rbac --name "front-door-purge-sp" --role "CDN Profile Contributor" --scopes /subscriptions/{your-subscription-id}
```

### 4. 运行程序

```bash
./run.sh
```

程序启动后会显示交互式选择界面：

```
🔧 选择操作模式:
1. 清除所有 endpoints 的缓存
2. 选择特定的 endpoints 清除缓存

请选择操作模式 (1 或 2): 
```

## 使用方式

### 交互式模式（推荐）

运行程序后根据提示选择操作：

1. **清除所有 endpoints**: 自动并行清除所有可用 endpoints 的缓存
2. **选择特定 endpoints**: 从列表中选择要清除缓存的 endpoints（支持多选）

### 并行处理优势

- **速度提升**: 多个 endpoints 同时处理，大幅减少总时间
- **进度跟踪**: 实时显示处理进度 `[1/5]`, `[2/5]`, `[3/5]`...
- **错误隔离**: 单个 endpoint 失败不影响其他 endpoints 的处理
- **资源控制**: 最多使用 5 个并行线程，避免过度占用资源

### 编程方式使用

```python
from purge_cache import AzureFrontDoorPurgeClient

client = AzureFrontDoorPurgeClient()

# 方式1: 并行清除多个指定的 endpoints
endpoints = ["endpoint1", "endpoint2", "endpoint3"]
results = client.purge_cache_parallel(endpoints)

# 方式2: 清除所有 endpoints（兼容旧版本）
client.purge_cache()

# 方式3: 清除指定 endpoint
client.purge_specific_endpoint("my-endpoint-name", ["/api/*", "/images/*"])

# 方式4: 列出所有可用 endpoints
client.list_endpoints()
```

### 性能对比

| 处理方式 | 5个Endpoints耗时 | 10个Endpoints耗时 |
|---------|-----------------|-------------------|
| 串行处理 | ~50秒 | ~100秒 |
| 并行处理 | ~10秒 | ~20秒 |
| **提升** | **5倍** | **5倍** |

## 自定义配置

### 清除路径配置

在 `.env` 文件中修改 `PURGE_PATHS`:

```env
# 清除所有内容
PURGE_PATHS=/*

# 清除特定路径
PURGE_PATHS=/api/*, /images/*, /css/*, /js/*

# 清除多个API版本
PURGE_PATHS=/api/v1/*, /api/v2/*, /static/*
```

## 权限要求

确保您的 Azure 服务主体具有以下权限：
- **CDN Profile Contributor** 角色（在订阅或资源组级别）

## 示例输出

### 单 Endpoint 场景
```
Azure Front Door Standard 缓存清除工具
==================================================
可用的 endpoints (1 个):
  1. my-endpoint - my-app.azurefd.net (状态: Succeeded)

开始清除 Front Door 'my-front-door' 的缓存...
使用 endpoint: my-endpoint
✅ 缓存清除操作完成!
```

### 多 Endpoint 场景
```
Azure Front Door Standard 缓存清除工具
==================================================
可用的 endpoints (3 个):
  1. web-endpoint - web.azurefd.net (状态: Succeeded)
  2. api-endpoint - api.azurefd.net (状态: Succeeded)
  3. cdn-endpoint - cdn.azurefd.net (状态: Succeeded)

📋 发现 3 个 endpoints，将逐个清除缓存...

[1/3] 正在清除 endpoint 'web-endpoint' 的缓存...
✅ Endpoint 'web-endpoint' 缓存清除成功

[2/3] 正在清除 endpoint 'api-endpoint' 的缓存...
✅ Endpoint 'api-endpoint' 缓存清除成功

[3/3] 正在清除 endpoint 'cdn-endpoint' 的缓存...
✅ Endpoint 'cdn-endpoint' 缓存清除成功

📊 缓存清除完成: 3/3 个 endpoints 成功
🎉 缓存清除操作成功完成!
```

## 如何确认缓存刷新成功？

### 1. 程序确认
程序成功执行后会显示：
- ✅ 每个 endpoint 的清除状态
- 📊 成功统计（如 "3/3 个 endpoints 成功"）
- 🎉 最终成功提示

### 2. 手动验证方法

#### 方法一：浏览器验证
1. **强制刷新页面**: Ctrl+F5 (Windows) 或 Cmd+Shift+R (Mac)
2. **开发者工具验证**:
   - 打开浏览器开发者工具 (F12)
   - 查看网络标签页
   - 检查响应头中的 `X-Cache` 字段
   - `MISS` 表示缓存已清除，`HIT` 表示使用缓存

#### 方法二：命令行验证
```bash
# 使用 curl 检查响应头
curl -I https://your-site.azurefd.net/

# 查看 X-Cache 和响应时间
curl -w "Time: %{time_total}s\n" -I https://your-site.azurefd.net/
```

#### 方法三：使用验证脚本
```bash
# 运行专门的验证工具
python verify_cache_refresh.py
```

### 3. 验证指标

| 指标 | 缓存清除前 | 缓存清除后 |
|------|------------|------------|
| **X-Cache** | HIT | MISS (然后逐渐变为 HIT) |
| **响应时间** | 较快 | 可能稍慢 (第一次请求) |
| **内容** | 旧版本 | 新版本 |
| **ETag** | 不变 | 可能改变 |

### 4. 常见验证场景

#### 网站内容更新后
```bash
# 1. 更新网站内容
# 2. 清除缓存
./run.sh

# 3. 验证内容是否更新
curl https://your-site.azurefd.net/ | grep "更新的内容"
```

#### API 接口更新后
```bash
# 清除 API 缓存
# PURGE_PATHS=/api/* ./run.sh

# 验证 API 响应
curl -H "Cache-Control: no-cache" https://your-api.azurefd.net/api/version
```

## 故障排除

### 常见错误

1. **认证失败**
   - 检查服务主体的 Client ID、Client Secret 和 Tenant ID
   - 确认服务主体具有正确的权限

2. **资源未找到**
   - 验证订阅 ID、资源组名称和 Front Door 名称
   - 确认资源存在于指定的订阅中

3. **条件访问策略阻止**
   - 联系 Azure 管理员调整条件访问策略
   - 或使用符合策略要求的环境运行

## 项目结构

```
.
├── purge_cache.py          # 主程序
├── requirements.txt        # Python 依赖
├── .env.example           # 配置模板
├── .env                   # 实际配置（需要填写）
├── run.sh                 # 启动脚本
├── .gitignore            # Git 忽略文件
├── README.md             # 说明文档
└── VERSION.md            # 版本信息
```

## 许可证

MIT License
