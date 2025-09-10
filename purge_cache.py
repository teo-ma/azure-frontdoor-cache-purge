#!/usr/bin/env python3
"""
Azure Front Door Standard 缓存清除工具

这个简单的 Python 程序用于清除 Azure Front Door Standard 的缓存。
使用 Azure 服务主体进行身份验证。

使用方法:
1. 复制 .env.example 为 .env 并填入实际的配置信息
2. 安装依赖: pip install -r requirements.txt
3. 运行: python purge_cache.py
"""

import os
import sys
from typing import List, Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.cdn import CdnManagementClient
from dotenv import load_dotenv
import time


class AzureFrontDoorPurgeClient:
    """Azure Front Door 缓存清除客户端"""
    
    def __init__(self):
        """初始化客户端"""
        # 加载环境变量
        load_dotenv()
        
        # 获取认证信息
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        
        # 获取 Front Door 配置
        self.resource_group_name = os.getenv('RESOURCE_GROUP_NAME')
        self.front_door_name = os.getenv('FRONT_DOOR_NAME')
        
        # 验证必需的环境变量
        self._validate_config()
        
        # 创建认证凭据
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        # 创建 CDN 管理客户端
        self.cdn_client = CdnManagementClient(
            credential=self.credential,
            subscription_id=self.subscription_id
        )
    
    def _validate_config(self):
        """验证配置是否完整"""
        required_vars = [
            'AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET',
            'AZURE_SUBSCRIPTION_ID', 'RESOURCE_GROUP_NAME', 'FRONT_DOOR_NAME'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"错误: 缺少以下环境变量: {', '.join(missing_vars)}")
            print("请复制 .env.example 为 .env 并填入正确的配置信息")
            sys.exit(1)
    
    def purge_cache(self, paths: Optional[List[str]] = None, purge_all_endpoints: bool = True) -> bool:
        """
        清除 Front Door 缓存
        
        Args:
            paths: 要清除的路径列表，如果为 None 则清除所有缓存
            purge_all_endpoints: 是否清除所有 endpoints 的缓存，默认为 True
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 如果没有指定路径，从环境变量获取或使用默认值
            if paths is None:
                env_paths = os.getenv('PURGE_PATHS', '/*')
                paths = [path.strip() for path in env_paths.split(',')]
            
            print(f"开始清除 Front Door '{self.front_door_name}' 的缓存...")
            print(f"资源组: {self.resource_group_name}")
            print(f"清除路径: {paths}")
            
            # 获取所有 endpoints
            endpoints = self._get_all_endpoints()
            if not endpoints:
                print("❌ 未找到任何可用的 endpoints")
                return False
            
            success_count = 0
            total_count = len(endpoints)
            
            if purge_all_endpoints and total_count > 1:
                print(f"📋 发现 {total_count} 个 endpoints，将逐个清除缓存...")
                
                for i, endpoint in enumerate(endpoints, 1):
                    print(f"\n[{i}/{total_count}] 正在清除 endpoint '{endpoint.name}' 的缓存...")
                    
                    if self._purge_single_endpoint(endpoint.name, paths):
                        success_count += 1
                        print(f"✅ Endpoint '{endpoint.name}' 缓存清除成功")
                    else:
                        print(f"❌ Endpoint '{endpoint.name}' 缓存清除失败")
                
                print(f"\n📊 缓存清除完成: {success_count}/{total_count} 个 endpoints 成功")
                return success_count == total_count
            else:
                # 只清除第一个 endpoint
                endpoint_name = endpoints[0].name
                print(f"使用 endpoint: {endpoint_name}")
                return self._purge_single_endpoint(endpoint_name, paths)
                
        except Exception as e:
            print(f"❌ 缓存清除操作失败: {str(e)}")
            return False
    
    def _get_all_endpoints(self) -> List:
        """获取所有可用的 endpoints"""
        try:
            endpoints = list(self.cdn_client.afd_endpoints.list_by_profile(
                resource_group_name=self.resource_group_name,
                profile_name=self.front_door_name
            ))
            return endpoints
        except Exception as e:
            print(f"获取 endpoints 列表时出错: {str(e)}")
            return []
    
    def _purge_single_endpoint(self, endpoint_name: str, paths: List[str]) -> bool:
        """清除单个 endpoint 的缓存"""
        try:
            # 发起缓存清除操作
            purge_operation = self.cdn_client.afd_endpoints.begin_purge_content(
                resource_group_name=self.resource_group_name,
                profile_name=self.front_door_name,
                endpoint_name=endpoint_name,
                contents={
                    "content_paths": paths
                }
            )
            
            print(f"⏳ 等待 endpoint '{endpoint_name}' 清除操作完成...")
            
            # 等待操作完成
            result = purge_operation.result()
            return True
            
        except Exception as e:
            print(f"❌ Endpoint '{endpoint_name}' 清除失败: {str(e)}")
            return False

    def list_endpoints(self):
        """列出所有可用的 endpoints"""
        try:
            print(f"正在获取 Front Door '{self.front_door_name}' 的 endpoints...")
            
            endpoints = self._get_all_endpoints()
            
            if endpoints:
                print(f"可用的 endpoints ({len(endpoints)} 个):")
                for i, endpoint in enumerate(endpoints, 1):
                    status = getattr(endpoint, 'provisioning_state', 'Unknown')
                    print(f"  {i}. {endpoint.name} - {endpoint.host_name} (状态: {status})")
                
                if len(endpoints) > 1:
                    print(f"\n💡 提示: 发现多个 endpoints，程序将默认清除所有 endpoints 的缓存")
            else:
                print("未找到任何 endpoints")
                
        except Exception as e:
                print(f"获取 endpoints 列表失败: {str(e)}")

    def purge_specific_endpoint(self, endpoint_name: str, paths: Optional[List[str]] = None) -> bool:
        """
        清除指定 endpoint 的缓存
        
        Args:
            endpoint_name: 要清除的 endpoint 名称
            paths: 要清除的路径列表
            
        Returns:
            bool: 操作是否成功
        """
        if paths is None:
            env_paths = os.getenv('PURGE_PATHS', '/*')
            paths = [path.strip() for path in env_paths.split(',')]
        
        print(f"开始清除指定 endpoint '{endpoint_name}' 的缓存...")
        print(f"清除路径: {paths}")
        
        return self._purge_single_endpoint(endpoint_name, paths)
def main():
    """主函数"""
    print("Azure Front Door Standard 缓存清除工具")
    print("=" * 50)
    
    try:
        # 创建客户端
        client = AzureFrontDoorPurgeClient()
        
        # 列出可用的 endpoints（可选）
        client.list_endpoints()
        print()
        
        # 执行缓存清除
        success = client.purge_cache()
        
        if success:
            print("\n🎉 缓存清除操作成功完成!")
        else:
            print("\n💥 缓存清除操作失败!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 程序执行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
