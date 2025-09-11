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
from typing import List, Optional, Dict, Tuple
from azure.identity import ClientSecretCredential
from azure.mgmt.cdn import CdnManagementClient
from dotenv import load_dotenv
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import threading


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
        
        # 线程锁用于控制输出
        self.print_lock = threading.Lock()
    
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
    
    def safe_print(self, message: str):
        """线程安全的打印函数"""
        with self.print_lock:
            print(message)

    def get_user_choice(self) -> Tuple[str, List[str]]:
        """
        获取用户选择的操作类型和要处理的 endpoints
        
        Returns:
            Tuple[str, List[str]]: (操作类型, endpoints列表)
        """
        print("\n🔧 选择操作模式:")
        print("1. 清除所有 endpoints 的缓存")
        print("2. 选择特定的 endpoints 清除缓存")
        
        while True:
            try:
                choice = input("\n请选择操作模式 (1 或 2): ").strip()
                if choice in ['1', '2']:
                    break
                else:
                    print("❌ 无效选择，请输入 1 或 2")
            except KeyboardInterrupt:
                print("\n操作被取消")
                sys.exit(0)
        
        # 获取所有 endpoints
        endpoints = self._get_all_endpoints()
        if not endpoints:
            print("❌ 未找到任何可用的 endpoints")
            sys.exit(1)
        
        if choice == '1':
            # 清除所有 endpoints
            endpoint_names = [endpoint.name for endpoint in endpoints]
            print(f"✅ 已选择清除所有 {len(endpoint_names)} 个 endpoints 的缓存")
            return "all", endpoint_names
        else:
            # 选择特定 endpoints
            print(f"\n📋 可用的 endpoints ({len(endpoints)} 个):")
            for i, endpoint in enumerate(endpoints, 1):
                status = getattr(endpoint, 'provisioning_state', 'Unknown')
                print(f"  {i}. {endpoint.name} - {endpoint.host_name} (状态: {status})")
            
            while True:
                try:
                    selections = input(f"\n请选择要清除缓存的 endpoints (输入序号，多个用逗号分隔，如: 1,3,5): ").strip()
                    if not selections:
                        print("❌ 请输入至少一个选择")
                        continue
                    
                    # 解析用户输入
                    selected_indices = []
                    for s in selections.split(','):
                        try:
                            idx = int(s.strip())
                            if 1 <= idx <= len(endpoints):
                                selected_indices.append(idx - 1)  # 转换为0基索引
                            else:
                                print(f"❌ 序号 {idx} 超出范围 (1-{len(endpoints)})")
                                raise ValueError()
                        except ValueError:
                            print(f"❌ 无效的序号: {s.strip()}")
                            raise ValueError()
                    
                    if selected_indices:
                        selected_endpoints = [endpoints[i].name for i in selected_indices]
                        print(f"✅ 已选择 {len(selected_endpoints)} 个 endpoints: {', '.join(selected_endpoints)}")
                        return "selected", selected_endpoints
                    else:
                        print("❌ 请至少选择一个 endpoint")
                        
                except (ValueError, KeyboardInterrupt):
                    if KeyboardInterrupt:
                        print("\n操作被取消")
                        sys.exit(0)
                    continue

    def purge_cache_parallel(self, endpoint_names: List[str], paths: Optional[List[str]] = None, max_workers: int = 5) -> Dict[str, bool]:
        """
        并行清除多个 endpoints 的缓存
        
        Args:
            endpoint_names: 要清除的 endpoint 名称列表
            paths: 要清除的路径列表，如果为 None 则清除所有缓存
            max_workers: 最大并行工作线程数
            
        Returns:
            Dict[str, bool]: endpoint 名称到操作结果的映射
        """
        # 如果没有指定路径，从环境变量获取或使用默认值
        if paths is None:
            env_paths = os.getenv('PURGE_PATHS', '/*')
            paths = [path.strip() for path in env_paths.split(',')]
        
        self.safe_print(f"🚀 开始并行清除 {len(endpoint_names)} 个 endpoints 的缓存...")
        self.safe_print(f"📁 清除路径: {paths}")
        self.safe_print(f"⚡ 最大并行线程数: {max_workers}")
        self.safe_print("=" * 60)
        
        results = {}
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_endpoint = {
                executor.submit(self._purge_single_endpoint_with_result, endpoint_name, paths): endpoint_name
                for endpoint_name in endpoint_names
            }
            
            # 收集结果
            completed = 0
            total = len(endpoint_names)
            
            for future in concurrent.futures.as_completed(future_to_endpoint):
                endpoint_name = future_to_endpoint[future]
                completed += 1
                
                try:
                    success = future.result()
                    results[endpoint_name] = success
                    
                    if success:
                        self.safe_print(f"✅ [{completed}/{total}] Endpoint '{endpoint_name}' 缓存清除成功")
                    else:
                        self.safe_print(f"❌ [{completed}/{total}] Endpoint '{endpoint_name}' 缓存清除失败")
                        
                except Exception as e:
                    results[endpoint_name] = False
                    self.safe_print(f"❌ [{completed}/{total}] Endpoint '{endpoint_name}' 清除时发生异常: {str(e)}")
        
        # 输出汇总结果
        self.safe_print("=" * 60)
        success_count = sum(1 for success in results.values() if success)
        self.safe_print(f"📊 并行缓存清除完成: {success_count}/{total} 个 endpoints 成功")
        
        if success_count < total:
            self.safe_print("\n❌ 失败的 endpoints:")
            for endpoint_name, success in results.items():
                if not success:
                    self.safe_print(f"   - {endpoint_name}")
        
        return results

    def _purge_single_endpoint_with_result(self, endpoint_name: str, paths: List[str]) -> bool:
        """
        清除单个 endpoint 的缓存（带线程安全输出）
        
        Args:
            endpoint_name: endpoint 名称
            paths: 要清除的路径列表
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.safe_print(f"⏳ 开始清除 endpoint '{endpoint_name}' 的缓存...")
            
            # 发起缓存清除操作
            purge_operation = self.cdn_client.afd_endpoints.begin_purge_content(
                resource_group_name=self.resource_group_name,
                profile_name=self.front_door_name,
                endpoint_name=endpoint_name,
                contents={
                    "content_paths": paths
                }
            )
            
            # 等待操作完成
            result = purge_operation.result()
            
            # 添加详细的成功确认信息
            self.safe_print(f"✅ Endpoint '{endpoint_name}' 缓存清除操作已提交并确认")
            self.safe_print(f"   📋 清除路径: {', '.join(paths)}")
            self.safe_print(f"   ⏰ 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            self.safe_print(f"❌ Endpoint '{endpoint_name}' 清除失败: {str(e)}")
            return False
    def purge_cache(self, paths: Optional[List[str]] = None, purge_all_endpoints: bool = True) -> bool:
        """
        清除 Front Door 缓存（保留原有功能以兼容性）
        
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
            
            if purge_all_endpoints and len(endpoints) > 1:
                # 使用并行清除
                endpoint_names = [endpoint.name for endpoint in endpoints]
                results = self.purge_cache_parallel(endpoint_names, paths)
                success_count = sum(1 for success in results.values() if success)
                return success_count == len(endpoints)
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
            
            # 添加更详细的成功确认信息
            print(f"✅ Endpoint '{endpoint_name}' 缓存清除操作已提交并确认")
            print(f"   📋 清除路径: {', '.join(paths)}")
            print(f"   ⏰ 完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
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
        
        # 获取用户选择
        operation_type, selected_endpoints = client.get_user_choice()
        
        # 获取要清除的路径
        env_paths = os.getenv('PURGE_PATHS', '/*')
        paths = [path.strip() for path in env_paths.split(',')]
        
        print(f"\n🚀 开始执行缓存清除操作...")
        print(f"📁 清除路径: {paths}")
        
        # 根据选择执行相应操作
        if len(selected_endpoints) == 1:
            # 单个 endpoint，直接清除
            success = client._purge_single_endpoint_with_result(selected_endpoints[0], paths)
            results = {selected_endpoints[0]: success}
        else:
            # 多个 endpoints，并行清除
            results = client.purge_cache_parallel(selected_endpoints, paths)
        
        # 统计结果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            print("\n🎉 所有缓存清除操作成功完成!")
            print(f"✅ 成功清除了 {success_count} 个 endpoints 的缓存")
            print("\n💡 验证缓存清除效果的方法:")
            print("1. 访问您的网站，检查内容是否为最新版本")
            print("2. 使用浏览器开发者工具查看响应头")
            print("3. 运行验证脚本: python verify_cache_refresh.py")
            print("4. 检查响应时间和 X-Cache 头的变化")
        else:
            print(f"\n⚠️  部分缓存清除操作失败!")
            print(f"📊 结果统计: {success_count}/{total_count} 个 endpoints 成功")
            
            if success_count > 0:
                print("\n✅ 成功的 endpoints:")
                for endpoint_name, success in results.items():
                    if success:
                        print(f"   - {endpoint_name}")
            
            if success_count < total_count:
                print("\n❌ 失败的 endpoints:")
                for endpoint_name, success in results.items():
                    if not success:
                        print(f"   - {endpoint_name}")
                        
                print("\n💡 建议:")
                print("1. 检查网络连接和权限配置")
                print("2. 重新运行程序重试失败的 endpoints")
                print("3. 查看详细的错误信息以诊断问题")
                
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 程序执行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
