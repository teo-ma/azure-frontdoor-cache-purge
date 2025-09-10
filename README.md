# Azure Front Door Standard 缓存清除工具

这是一个简单的 Python 程序，用于清除 Azure Front Door Standard 的缓存，使用 Azure 服务主体进行身份验证。

## 功能特性

- 🔐 使用 Azure 服务主体进行安全认证
- 🚀 支持清除指定路径的缓存
- 📋 自动列出可用的 endpoints
- 🔄 **支持多 Endpoint 缓存清除** - 自动清除所有 endpoints 或指定 endpoint
- ⚙️ 通过环境变量进行配置
- 📝 详细的操作日志和错误处理

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

## 多 Endpoint 支持

当您的 Azure Front Door 有多个 endpoints 时：

- **默认行为**: 自动清除所有 endpoints 的缓存
- **显示进度**: 逐个清除并显示进度 `[1/3]`, `[2/3]`, `[3/3]`
- **错误处理**: 某个 endpoint 失败时继续处理其他 endpoints
- **成功统计**: 显示成功清除的 endpoints 数量

### 编程方式使用

```python
from purge_cache import AzureFrontDoorPurgeClient

client = AzureFrontDoorPurgeClient()

# 清除所有 endpoints（默认）
client.purge_cache()

# 只清除第一个 endpoint
client.purge_cache(purge_all_endpoints=False)

# 清除指定 endpoint
client.purge_specific_endpoint("my-endpoint-name", ["/api/*", "/images/*"])
```

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
