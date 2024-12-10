import subprocess
import sys
import os

def setup_environment():
    try:
        # 检查是否在虚拟环境中
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("请在虚拟环境中运行此脚本！")
            return False
            
        # 升级pip
        print("正在升级pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # 安装requirements.txt中的包
        print("正在安装依赖包...")
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        
        print("\n所有依赖包安装完成！")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"安装过程中出错: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

if __name__ == "__main__":
    setup_environment() 