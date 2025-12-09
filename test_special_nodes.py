#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特殊节点集成功能
"""

import sys
import os
sys.path.append('.')

from src.core.ServerManager import ServerManager
from src.core.PingService import PingService
from src.network.PingUtils import ping_host, test_tcp_port

def test_special_nodes():
    """测试特殊节点功能"""
    print("=" * 60)
    print("特殊节点集成测试")
    print("=" * 60)
    
    # 1. 测试服务器列表加载
    print("\n1. 服务器列表加载测试")
    manager = ServerManager()
    servers = manager.get_servers()
    
    print(f"  服务器总数: {len(servers)}")
    special_nodes = []
    for name, (host, port, token) in servers.items():
        if "特殊节点" in name:
            special_nodes.append((name, host, port))
            print(f"  ✓ {name}: {host}:{port} (特殊节点)")
        else:
            print(f"  • {name}: {host}:{port}")
    
    # 2. 测试Ping功能
    print("\n2. Ping功能测试")
    ping_service = PingService(max_workers=5)
    results = {}
    for name, delay in ping_service.ping_servers(servers):
        results[name] = delay
    
    for name, delay in results.items():
        if delay:
            print(f"  ✓ {name}: {delay}ms")
        else:
            print(f"  ✗ {name}: 超时")
    
    # 3. 测试特殊节点详细连通性
    print("\n3. 特殊节点详细测试")
    for name, host, port in special_nodes:
        print(f"\n  {name} ({host}:{port}):")
        
        # ICMP Ping
        icmp_result = ping_host(host)
        if icmp_result:
            print(f"    ICMP Ping: ✓ {icmp_result}ms")
        else:
            print(f"    ICMP Ping: ✗ 失败")
        
        # TCP端口测试
        tcp_result = test_tcp_port(host, port, timeout=3)
        if tcp_result['success']:
            print(f"    TCP端口{port}: ✓ {tcp_result['latency']}ms")
        else:
            print(f"    TCP端口{port}: ✗ {tcp_result['error']}")
    
    # 4. 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  总服务器数: {len(servers)}")
    print(f"  特殊节点数: {len(special_nodes)}")
    
    all_special_nodes_ok = True
    for name, host, port in special_nodes:
        if name in results and results[name]:
            print(f"  ✓ {name}: Ping正常 ({results[name]}ms)")
        else:
            print(f"  ✗ {name}: Ping失败")
            all_special_nodes_ok = False
    
    if all_special_nodes_ok:
        print("\n✅ 所有特殊节点测试通过!")
    else:
        print("\n❌ 部分特殊节点测试失败!")
    
    print("=" * 60)

if __name__ == "__main__":
    test_special_nodes()