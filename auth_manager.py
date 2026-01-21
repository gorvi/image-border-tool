
import os
import json
import uuid
import hashlib
import base64
import platform
import requests
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

# 简单的混淆存储路径
CONFIG_FILE = os.path.expanduser('~/.tupian_auth_data')

# Server Configuration
LICENSE_SERVER_URL = "http://127.0.0.1:8000"  # TODO: Change to production URL
RSA_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA5uPXQrj0Cc4M8ndXLn30
xvsafvrJr6j7yQ49kCKrrEuspw2jfHVRdITU0sgt2lDcUr24l1I9i8JKMFrx2dvk
P3+UVCR/DS7IA96A1OR7VwL1goZtm8/RKhaTz04lhIB2s3y/Oy0GyfteVy+W7/BF
F/41D9OYvFKjMkOml+OMZSmfqxSDXAuGzviGz0hzPmXpS/LS9M70dujmGbtbso6f
uWOOQVpXUES+EbYFb7t3L7qXWZgsAFzoS1grUe+q6OHhacuVltilr9qx2GKP1u6U
xeNPv2XUON28BEqLjGLlao3KPsaMRw48AfndkMmqNsgmEJEbrIlTLTsgqWXss+6N
kQIDAQAB
-----END PUBLIC KEY-----"""

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
            'usage_count': 0, 
            'daily_usage': {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0},
            'license_key': None,
            'is_activated': False,
            'license_type': 'free',  # free, monthly, yearly, permanent
            'expires_at': None,      # ISO format string
            'signature': None,       # RSA signature
            't_max_seen': datetime.now().isoformat(),  # 记录见过的最晚时间 (防止改系统时间)
            'is_time_tampered': False, # 是否由于时间篡改被锁定
            'failed_attempts': 0,      # 激活失败次数
            'cooldown_until': None     # 冷却截止时间 (ISO)
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    # 迁移旧数据
                    if 'daily_usage' not in data:
                        data['daily_usage'] = {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0}
                    if 't_max_seen' not in data:
                        data['t_max_seen'] = datetime.now().isoformat()
                    if 'is_time_tampered' not in data:
                        data['is_time_tampered'] = False
                    if 'failed_attempts' not in data:
                        data['failed_attempts'] = 0
                    if 'cooldown_until' not in data:
                        data['cooldown_until'] = None
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

    def _get_current_time(self):
        """
        获取可靠的当前时间:
        1. 尝试网络对时 (静默)
        2. 如果失败，使用本地时间
        3. 检查是否发生时间倒补
        """
        now = datetime.now()
        
        # 1. 尝试网络对时 (Baidu 或 WorldTimeAPI)
        try:
            # 简单 HEAD 请求获取 Server Header 中的时间 (非常快)
            resp = requests.head("https://www.baidu.com", timeout=2)
            if 'Date' in resp.headers:
                # 转换 HTTP 日期格式: "Mon, 20 Jan 2026 01:23:45 GMT"
                from email.utils import parsedate_to_datetime
                net_now = parsedate_to_datetime(resp.headers['Date'])
                # 转换为本地时区 (如果有必要)
                now = net_now.replace(tzinfo=None) + timedelta(hours=8) # 默认东八区
        except:
            pass # 网络不可用或超时，回退到系统时间

        # 2. 检查篡改机制 (针对断网环境)
        t_max_iso = self.data.get('t_max_seen')
        if t_max_iso:
            t_max = datetime.fromisoformat(t_max_iso)
            # 允许 1 小时的微小误差（由于关机或系统校准）
            if now < (t_max - timedelta(hours=1)):
                self.data['is_time_tampered'] = True
                self._save_data()
                return t_max # 强制返回见过的最晚时间

        # 3. 更新见过的最晚时间
        if now > datetime.fromisoformat(self.data.get('t_max_seen', now.isoformat())):
            self.data['t_max_seen'] = now.isoformat()
            self._save_data()
            
        return now

    def get_status(self):
        """获取当前状态"""
        # 0. 检查是否被时间锁定
        if self.data.get('is_time_tampered'):
            return {'status': 'locked', 'msg': '由于检测到系统时间异常（往前调整），授权已被锁定。请恢复正常时间。'}

        # 获取可靠的时间
        current_now = self._get_current_time()

        # Prioritize Verified Activated Status
        if self.data.get('is_activated'):
            # Check expiration if not permanent
            if self.data.get('expires_at'):
                expires = datetime.fromisoformat(self.data['expires_at'])
                days_left = (expires - current_now).days
                if days_left < 0:
                    return {'status': 'expired', 'msg': '授权已过期', 'days_left': 0}
                return {'status': 'activated', 'msg': f"已激活 ({self.data.get('license_type')}) - 剩余 {days_left} 天", 'days_left': days_left}
            return {'status': 'activated', 'msg': '永久激活 (无限制)', 'days_left': 9999}
        
        # 1. 检查3天体验期
        install_date = datetime.strptime(self.data['install_date'], '%Y-%m-%d')
        days_passed = (current_now - install_date).days
        remaining_trial_days = 3 - days_passed
        
        if remaining_trial_days >= 0:
             return {'status': 'trial', 'msg': f'全功能体验期 (剩余 {remaining_trial_days + 1} 天)'}
        
        # 2. 体验期结束 -> 免费版 (每日5张)
        self._check_daily_reset(current_now)
        daily_count = self.data['daily_usage']['count']
        remaining_daily = 5 - daily_count
        
        if remaining_daily > 0:
            return {'status': 'free', 'msg': f'免费版 (今日剩余 {remaining_daily} 张)', 'daily_left': remaining_daily}
        else:
            return {'status': 'limited', 'msg': '今日免费额度已用完 (5/5)', 'daily_left': 0}

    def _check_daily_reset(self, current_now=None):
        """检查是否跨天重置"""
        if current_now is None:
            current_now = self._get_current_time()
        today = current_now.strftime('%Y-%m-%d')
        if self.data['daily_usage']['date'] != today:
            self.data['daily_usage'] = {'date': today, 'count': 0}
            self._save_data()

    def increment_usage(self, count=1):
        """增加使用计数，返回 (是否允许, 提示信息)"""
        # 获取可靠时间
        current_now = self._get_current_time()
        
        if self.data.get('is_activated'):
            # Check expiration again to be safe
            status = self.get_status()
            if status['status'] == 'locked':
                return False, status['msg']
            if status['status'] == 'expired':
                return False, "授权已过期，请重新激活。"
            return True, "Success"
            
        # 检查是否在体验期
        install_date = datetime.strptime(self.data['install_date'], '%Y-%m-%d')
        if (current_now - install_date).days <= 3:
            self.data['usage_count'] = self.data.get('usage_count', 0) + count
            self._save_data()
            return True, "Trial"

        # 免费版限制
        self._check_daily_reset(current_now)
        daily_count = self.data['daily_usage']['count']
        
        if daily_count + count <= 5:
            self.data['daily_usage']['count'] += count
            self.data['usage_count'] = self.data.get('usage_count', 0) + count
            self._save_data()
            return True, "Free"
        else:
            return False, "今日免费导出额度(5张)已用完，请激活软件解除限制。"

    def verify_signature(self, data_str, signature_b64):
        """验证 RSA 签名"""
        try:
            public_key = serialization.load_pem_public_key(RSA_PUBLIC_KEY_PEM.encode())
            signature = base64.b64decode(signature_b64)
            data = data_str.encode()
            
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            print("Invalid Signature")
            return False
        except Exception as e:
            print(f"Verification Error: {e}")
            return False

    def activate_online(self, license_code):
        """在线激活"""
        current_now = self._get_current_time()

        # 1. 检查本地冷却时间
        cooldown_until_iso = self.data.get('cooldown_until')
        if cooldown_until_iso:
            cooldown_until = datetime.fromisoformat(cooldown_until_iso)
            if current_now < cooldown_until:
                wait_secs = int((cooldown_until - current_now).total_seconds())
                return False, f"尝试次数过多，请在 {wait_secs} 秒后重试。"

        license_code = license_code.strip()
        payload = {
            "code": license_code,
            "machine_id": self.machine_code,
            "app_id": "1001"  # Updated to numeric App ID 1001
        }
        
        try:
            # URL Structure: /api/v1/{app_id}/activate
            response = requests.post(
                f"{LICENSE_SERVER_URL}/api/v1/{payload['app_id']}/activate", 
                json=payload, 
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Check server logic status first
            if result.get("status") != "activated":
                # 记录失败并增加冷却
                self.data['failed_attempts'] += 1
                # 失败 3 次以上触发冷却，每次增加 (失败次数-2) * 60 秒
                if self.data['failed_attempts'] >= 3:
                    cd_seconds = (self.data['failed_attempts'] - 2) * 60
                    self.data['cooldown_until'] = (current_now + timedelta(seconds=cd_seconds)).isoformat()
                self._save_data()
                return False, result.get("message", "激活失败")
            
            # 1. Verify Signature
            license_type = result.get("license_type")
            expires_at = result.get("expires_at", "")
            
            # Use the EXACT ISO string from the response, because server signs that.
            sign_data = f"1001|{self.machine_code}|{license_type}|{expires_at}"
            
            if self.verify_signature(sign_data, result["signature"]):
                # Success & Verified
                self.data['is_activated'] = True
                self.data['license_key'] = license_code
                self.data['license_type'] = license_type
                self.data['expires_at'] = expires_at
                self.data['signature'] = result["signature"]
                # 成功后重置失败计数
                self.data['failed_attempts'] = 0
                self.data['cooldown_until'] = None
                self._save_data()
                return True, "激活成功！"
            else:
                return False, "激活失败：服务器签名验证未通过（数据可能被篡改）。"
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return False, "服务器繁忙（请求过于频繁），请稍后再试。"
            
            if hasattr(e.response, 'json'):
                try:
                    err_msg = e.response.json().get('detail', str(e))
                    return False, f"激活失败: {err_msg}"
                except:
                    pass
            return False, f"HTTP错误: {str(e)}"
        except requests.exceptions.RequestException as e:
            return False, f"网络连接失败: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def get_activation_info(self):
        return {
            'machine_code': self.machine_code,
            'status': self.get_status()
        }

    def get_ui_config(self):
        """获取动态 UI 配置"""
        app_id = "1001"
        try:
            # 增加 timeout 防止网络阻塞主线程太久
            response = requests.get(f"{LICENSE_SERVER_URL}/api/v1/1001/config", timeout=3)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        # 默认硬编码配置 (作为网络失败时的兜底)
        return {
            "ui_title": "软件授权激活",
            "ui_promo_text": "🔥 限量特惠进行中",
            "ui_slogan": "成功源于坚持，灵感来自创作",
            "ui_pricing": [
                 {"name": "月卡会员", "price": "9.9", "old_price": "19.8", "desc": "折合每日仅需 0.3 元", "url": "https://your-shop-url.com/buy/monthly"},
                 {"name": "年卡会员", "price": "59", "old_price": "168", "desc": "折合每日仅需 0.16 元", "url": "https://your-shop-url.com/buy/yearly"},
                 {"name": "三年(新年特惠)", "price": "99", "old_price": "328", "desc": "限量特惠：每日不到 0.1 元", "url": "https://your-shop-url.com/buy/three-year"}
            ]
        }

    def get_usage_stats(self):
        """获取详细用量统计"""
        return {
            'total_count': self.data.get('usage_count', 0),
            'install_date': self.data.get('install_date', 'Unknown'),
            'daily_count': self.data.get('daily_usage', {}).get('count', 0),
            'daily_date': self.data.get('daily_usage', {}).get('date', 'Unknown'),
            'is_activated': self.data.get('is_activated', False),
            'license_type': self.data.get('license_type', 'Free'),
            'expires_at': self.data.get('expires_at', 'N/A')
        }

# 单例
auth = AuthManager()

if __name__ == '__main__':
    # 测试打印
    print(f"Machine Code: {auth.machine_code}")
    print(f"Status: {auth.get_status()}")

