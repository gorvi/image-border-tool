
import os
import json
import time
from datetime import datetime, timedelta
from auth_manager import AuthManager
import auth_manager as am

def test_rate_limiting():
    print("=== 开始测试激活限流机制 (Rate Limiting Test) ===")
    
    # 1. 准备测试环境
    test_config = os.path.expanduser('~/.tupian_auth_data_rate_test')
    original_config = am.CONFIG_FILE
    am.CONFIG_FILE = test_config
    
    # 清理旧数据
    if os.path.exists(test_config):
        os.remove(test_config)
        
    auth = AuthManager()
    
    print(f"1. 初始化测试环境，机器码: {auth.machine_code}")
    
    # 2. 模拟连续失败激活
    print("\n2. 模拟连续输入错误激活码...")
    for i in range(1, 4):
        print(f"   尝试第 {i} 次激活 (使用错误码 'WRONG-CODE-{i}')...")
        success, msg = auth.activate_online(f"WRONG-CODE-{i}")
        print(f"   结果: {'成功' if success else '失败'} | 提示: {msg}")
        
    # 3. 检查是否触发了本地冷却
    print("\n3. 触发第 4 次尝试，检查本地冷却状态...")
    success, msg = auth.activate_online("WRONG-CODE-4")
    print(f"   最终结果: {'成功' if success else '失败'}")
    print(f"   日志/提示: {msg}")
    
    if "重试" in msg:
        print("\n✅ 客户端防刷测试成功：连续失败 3 次后，本地已进入冷却锁定。")
    else:
        print("\n❌ 客户端防刷测试失败：未能触发本地冷却。")

    # 4. 环境还原
    am.CONFIG_FILE = original_config
    if os.path.exists(test_config):
        os.remove(test_config)
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_rate_limiting()
