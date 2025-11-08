# install_module_simple.py
import subprocess
import sys

def install_from_requirements():
    """
    从requirements.txt文件安装依赖
    """
    # 创建requirements.txt文件
    requirements = """Flask==2.3.3
reportlab==4.0.4
Werkzeug==2.3.7"""
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    
    print("正在从requirements.txt安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 所有依赖安装完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装失败: {e}")
        return False

if __name__ == "__main__":
    install_from_requirements()
