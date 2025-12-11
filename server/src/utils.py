from fastapi import Request
import ipaddress
from typing import List, Union

def get_effective_ip(request: Request) -> str:
    """
    获取客户端真实IP，兼容 Nginx 反代 (X-Forwarded-For, X-Real-IP)。
    """
    # 优先检查 X-Forwarded-For
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # 取第一个IP
        return x_forwarded_for.split(",")[0].strip()
    
    # 其次检查 X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip
        
    # 最后使用直连IP
    return request.client.host or "127.0.0.1"

def mask_ip(ip: str) -> str:
    """
    脱敏IP地址，隐藏最后一段（D段）。
    例如：192.168.1.100 -> 192.168.1.***
    """
    if not ip:
        return "***.***.***"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    # IPv6 或异常格式
    return ip[:len(ip)//2] + "***"

def parse_ip_rule(rule_str: str) -> List[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
    """
    解析 IP 规则字符串，支持 CIDR、范围(-)、列表(,)。
    例如: "192.168.1.0/24, 10.0.0.1-10.0.0.5, 1.1.1.1"
    """
    networks = []
    if not rule_str:
        return networks
        
    parts = rule_str.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        try:
            if '-' in part:
                # Range: 1.1.1.1-1.1.1.5
                start, end = part.split('-', 1)
                start_ip = ipaddress.ip_address(start.strip())
                end_ip = ipaddress.ip_address(end.strip())
                # summarize_address_range return an iterator
                networks.extend(list(ipaddress.summarize_address_range(start_ip, end_ip)))
            else:
                # CIDR or Single IP
                networks.append(ipaddress.ip_network(part, strict=False))
        except ValueError:
            # 忽略无效的规则部分
            continue
    return networks

def is_ip_matched(ip_str: str, rules: List[str]) -> bool:
    """
    检查 IP 是否匹配给定的规则列表
    :param ip_str: 目标 IP
    :param rules: 规则字符串列表 (e.g. ["192.168.1.0/24", "10.0.0.1-10.0.0.5"])
    :return: True if matched
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        for rule in rules:
            networks = parse_ip_rule(rule)
            for net in networks:
                if ip in net:
                    return True
    except ValueError:
        return False
    return False

