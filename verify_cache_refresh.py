#!/usr/bin/env python3
"""
Azure Front Door 缓存刷新验证工具

这个脚本帮助您验证缓存刷新是否真正生效。
"""

import requests
import time
from datetime import datetime
from typing import List, Dict

def test_cache_refresh(urls: List[str], test_iterations: int = 3) -> Dict:
    """
    测试缓存刷新效果
    
    Args:
        urls: 要测试的URL列表
        test_iterations: 测试次数
    
    Returns:
        测试结果字典
    """
    results = {}
    
    print("🧪 开始缓存刷新验证测试")
    print("=" * 50)
    
    for url in urls:
        print(f"\n🔍 测试 URL: {url}")
        results[url] = []
        
        for i in range(test_iterations):
            try:
                print(f"  第 {i+1} 次请求...")
                
                # 发起HTTP请求
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                # 获取响应头信息
                headers_info = {
                    'status_code': response.status_code,
                    'response_time': round(response_time * 1000, 2),  # 毫秒
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'cache_control': response.headers.get('Cache-Control', 'N/A'),
                    'etag': response.headers.get('ETag', 'N/A'),
                    'last_modified': response.headers.get('Last-Modified', 'N/A'),
                    'x_cache': response.headers.get('X-Cache', 'N/A'),
                    'x_azure_ref': response.headers.get('X-Azure-Ref', 'N/A'),
                    'content_length': response.headers.get('Content-Length', 'N/A')
                }
                
                results[url].append(headers_info)
                
                print(f"    ✅ 状态: {headers_info['status_code']}, "
                      f"响应时间: {headers_info['response_time']}ms, "
                      f"X-Cache: {headers_info['x_cache']}")
                
                # 间隔一段时间
                if i < test_iterations - 1:
                    time.sleep(2)
                    
            except requests.RequestException as e:
                error_info = {
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                results[url].append(error_info)
                print(f"    ❌ 请求失败: {str(e)}")
    
    return results

def analyze_results(results: Dict) -> None:
    """分析测试结果"""
    print("\n" + "=" * 50)
    print("📊 缓存刷新验证结果分析")
    print("=" * 50)
    
    for url, tests in results.items():
        print(f"\n🌐 URL: {url}")
        print("-" * 40)
        
        # 统计成功的请求
        successful_tests = [t for t in tests if 'status_code' in t]
        
        if not successful_tests:
            print("❌ 所有请求都失败了")
            continue
        
        # 分析响应时间变化
        response_times = [t['response_time'] for t in successful_tests]
        avg_response_time = sum(response_times) / len(response_times)
        
        print(f"✅ 成功请求: {len(successful_tests)}/{len(tests)}")
        print(f"📈 平均响应时间: {avg_response_time:.2f}ms")
        
        # 分析缓存头变化
        cache_headers = [t.get('x_cache', 'N/A') for t in successful_tests]
        unique_cache_states = set(cache_headers)
        
        print(f"💾 Cache 状态变化: {list(unique_cache_states)}")
        
        # 分析 ETag 变化
        etags = [t.get('etag', 'N/A') for t in successful_tests]
        unique_etags = set(etags)
        
        if len(unique_etags) > 1:
            print("🔄 检测到内容变化 (ETag不同)")
        else:
            print("📌 内容未变化 (ETag相同)")
        
        # 显示详细信息
        print("\n详细请求信息:")
        for i, test in enumerate(successful_tests, 1):
            print(f"  {i}. {test['timestamp']} - "
                  f"状态:{test['status_code']} - "
                  f"时间:{test['response_time']}ms - "
                  f"Cache:{test.get('x_cache', 'N/A')}")

def get_front_door_urls() -> List[str]:
    """获取要测试的Front Door URLs"""
    print("🔗 请输入要测试的 Front Door URLs")
    print("提示: 输入完整的URL，例如 https://your-site.azurefd.net/")
    print("输入空行结束\n")
    
    urls = []
    while True:
        url = input(f"URL {len(urls)+1}: ").strip()
        if not url:
            break
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        urls.append(url)
    
    return urls

def main():
    """主函数"""
    print("Azure Front Door 缓存刷新验证工具")
    print("=" * 50)
    print("这个工具帮助您验证缓存刷新是否生效")
    print("建议在执行缓存清除操作前后运行此工具进行对比\n")
    
    # 获取测试URLs
    urls = get_front_door_urls()
    
    if not urls:
        print("❌ 没有提供测试URL")
        return
    
    print(f"\n📋 将测试以下URLs: {urls}")
    
    # 询问测试次数
    try:
        iterations = int(input("\n🔢 测试次数 (默认3次): ") or "3")
    except ValueError:
        iterations = 3
    
    print(f"\n🚀 开始执行 {iterations} 次测试...")
    
    # 执行测试
    results = test_cache_refresh(urls, iterations)
    
    # 分析结果
    analyze_results(results)
    
    print("\n" + "=" * 50)
    print("💡 验证提示:")
    print("1. 如果响应时间明显变化，可能表示缓存已刷新")
    print("2. X-Cache 头从 HIT 变为 MISS 表示缓存已清除")
    print("3. ETag 或 Last-Modified 变化表示内容已更新")
    print("4. 建议在缓存清除前后各运行一次此工具进行对比")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
