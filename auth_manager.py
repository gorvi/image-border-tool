
import os
import json
import uuid
import hashlib
import base64
import platform
from datetime import datetime, timedelta

# 简单的混淆存储路径
CONFIG_FILE = os.path.expanduser('~/.tupian_auth_data')
SECRET_SALT = "TUPIAN_2026_SECRET_KEY_!@#" # 用于生成激活码的盐

class AuthManager:
    def __init__(self):
        self.machine_code = self._generate_machine_code()
        self.data = self._load_data()
        
    def _generate_machine_code(self):
        """生成固定的机器码 (基于 MAC 地址和系统信息)"""
        mac = uuid.getnode()
        system_info = f"{platform.system()}-{platform.node()}-{platform.processor()}"
        raw_id = f"{mac}-{system_info}"
        hash_bytes = hashlib.md5(raw_id.encode()).digest()
        b64_str = base64.b32encode(hash_bytes).decode().replace('=', '')
        return b64_str[:12]

    def _load_data(self):
        """加载授权数据"""
        default_data = {
            'install_date': datetime.now().strftime('%Y-%m-%d'),
            'usage_count': 0, # 总使用数 (保留但不做硬限制)
            'daily_usage': {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0},
            'license_key': None,
            'is_activated': False
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # 迁移旧数据
                    if 'daily_usage' not in data:
                        data['daily_usage'] = {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0}
                    return data
            except:
                pass
        return default_data

    def _save_data(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Auth save failed: {e}")

    def get_status(self):
        """获取当前状态"""
        if self.data.get('is_activated'):
            return {'status': 'activated', 'msg': '永久激活 (无限制)'}
        
        # 1. 检查3天体验期
        install_date = datetime.strptime(self.data['install_date'], '%Y-%m-%d')
        days_passed = (datetime.now() - install_date).days
        remaining_trial_days = 3 - days_passed
        
        if remaining_trial_days >= 0:
             return {'status': 'trial', 'msg': f'全功能体验期 (剩余 {remaining_trial_days + 1} 天)'}
        
        # 2. 体验期结束 -> 免费版 (每日5张)
        self._check_daily_reset()
        daily_count = self.data['daily_usage']['count']
        remaining_daily = 5 - daily_count
        
        if remaining_daily > 0:
            return {'status': 'free', 'msg': f'免费版 (今日剩余 {remaining_daily} 张)', 'daily_left': remaining_daily}
        else:
            return {'status': 'limited', 'msg': '今日免费额度已用完 (5/5)', 'daily_left': 0}

    def _check_daily_reset(self):
        """检查是否跨天重置"""
        today = datetime.now().strftime('%Y-%m-%d')
        if self.data['daily_usage']['date'] != today:
            self.data['daily_usage'] = {'date': today, 'count': 0}
            self._save_data()

    def increment_usage(self, count=1):
        """增加使用计数，返回 (是否允许, 提示信息)"""
        if self.data.get('is_activated'):
            return True, "Success"
            
        # 检查是否在体验期
        install_date = datetime.strptime(self.data['install_date'], '%Y-%m-%d')
        if (datetime.now() - install_date).days <= 3:
            # 体验期由它去，但也记录一下
            self.data['usage_count'] = self.data.get('usage_count', 0) + count
            self._save_data()
            return True, "Trial"

        # 免费版限制
        self._check_daily_reset()
        daily_count = self.data['daily_usage']['count']
        
        if daily_count + count <= 5:
            self.data['daily_usage']['count'] += count
            self.data['usage_count'] = self.data.get('usage_count', 0) + count
            self._save_data()
            return True, "Free"
        else:
            return False, "今日免费导出额度(5张)已用完，请激活软件解除限制。"

    def validate_activation_code(self, input_code):
        input_code = input_code.strip().upper()
        expected_code = self._generate_expected_code().upper()
        
        if input_code == expected_code:
            self.data['is_activated'] = True
            self.data['license_key'] = input_code
            self._save_data()
            return True
        return False

    def _generate_expected_code(self):
        raw = f"{self.machine_code}{SECRET_SALT}"
        hash_str = hashlib.md5(raw.encode()).hexdigest()
        return hash_str[:16].upper()

    def get_activation_info(self):
        return {
            'machine_code': self.machine_code,
            'status': self.get_status()
        }

    def get_usage_stats(self):
        """获取详细用量统计"""
        return {
            'total_count': self.data.get('usage_count', 0),
            'install_date': self.data.get('install_date', 'Unknown'),
            'daily_count': self.data.get('daily_usage', {}).get('count', 0),
            'daily_date': self.data.get('daily_usage', {}).get('date', 'Unknown'),
            'is_activated': self.data.get('is_activated', False)
        }

# 单例
auth = AuthManager()

if __name__ == '__main__':
    # 测试打印
    print(f"Machine Code: {auth.machine_code}")
    print(f"Expected Key: {auth._generate_expected_code()}")
    print(f"Status: {auth.get_status()}")
