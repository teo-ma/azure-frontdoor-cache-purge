#!/bin/bash

# Azure Front Door 缓存清除工具启动脚本

echo "Azure Front Door Standard 缓存清除工具"
echo "========================================="

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
    echo "安装依赖包..."
    source venv/bin/activate
    pip install -r requirements.txt
    echo "虚拟环境创建完成！"
    echo
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 配置文件"
    echo "正在复制配置文件模板..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑此文件并填入您的 Azure 配置信息"
    echo
    echo "需要配置的信息："
    echo "- AZURE_TENANT_ID: Azure AD 租户 ID"
    echo "- AZURE_CLIENT_ID: 服务主体客户端 ID"
    echo "- AZURE_CLIENT_SECRET: 服务主体客户端密钥"
    echo "- AZURE_SUBSCRIPTION_ID: Azure 订阅 ID"
    echo "- RESOURCE_GROUP_NAME: 资源组名称"
    echo "- FRONT_DOOR_NAME: Front Door 名称"
    echo
    echo "配置完成后请重新运行此脚本。"
    exit 1
fi

# 运行程序
echo "运行缓存清除程序..."
echo
python purge_cache.py
