import hashlib

def generate_key(machine_code):
    """
    根据机器码生成激活码
    算法: MD5(MachineCode + Salt) 的前 16 位 (全大写)
    """
    SECRET_SALT = "TUPIAN_2026_SECRET_KEY_!@#"
    raw = f"{machine_code}{SECRET_SALT}"
    hash_str = hashlib.md5(raw.encode()).hexdigest()
    return hash_str[:16].upper()

if __name__ == "__main__":
    print("=== 图片套版工具 - 激活码生成器 ===")
    while True:
        machine_code = input("\n请输入用户提供的机器码 (输入 q 退出): ").strip()
        if machine_code.lower() == 'q':
            break
        if not machine_code:
            continue
            
        key = generate_key(machine_code)
        print(f"✅ 激活码: {key}")
        print("-" * 30)
