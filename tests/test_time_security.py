
import os
import json
import time
from datetime import datetime, timedelta
from auth_manager import AuthManager

def test_time_anti_tampering():
    print("=== 开始测试时间防篡改机制 ===")
    
    # 1. 模拟一个初始授权文件，记录一个未来的 "t_max_seen"
    test_config = os.path.expanduser('~/.tupian_auth_data_test')
    initial_data = {
        'install_date': '2026-01-01',
        'is_activated': True,
        'license_type': 'monthly',
        'expires_at': (datetime.now() + timedelta(days=30)).isoformat(),
        't_max_seen': (datetime.now() + timedelta(days=1)).isoformat(), # 模拟用户已经运行到了明天
        'is_time_tampered': False
    }
    
    with open(test_config, 'w') as f:
        json.dump(initial_data, f)
    
    print(f"1. 已创建测试配置文件，模拟其见过的最晚时间为: {initial_data['t_max_seen']}")
    
    # 2. 实例化 AuthManager 并指向测试配置
    import auth_manager as am
    original_config = am.CONFIG_FILE
    am.CONFIG_FILE = test_config
    
    auth = AuthManager()
    
    # 3. 检查当前状态 (此时系统时间应该比 t_max_seen 早，触发锁定)
    status = auth.get_status()
    print(f"2. 当前检测状态: {status['status']}")
    print(f"   提示信息: {status['msg']}")
    
    if status['status'] == 'locked':
        print("✅ 测试成功：成功检测到时间倒流并锁定授权。")
    else:
        print("❌ 测试失败：未能检测到时间倒流。")
        
    # 4. 测试网络对时 (模拟)
    print("\n3. 测试网络对时逻辑...")
    # 尝试调用内部方法
    real_time = auth._get_current_time()
    print(f"   当前获取的可靠时间: {real_time}")
    
    # 还原
    am.CONFIG_FILE = original_config
    if os.path.exists(test_config):
        os.remove(test_config)
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_time_anti_tampering()
