#!/usr/bin/env python3
"""Install missing dependencies for main.py"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip with fallback strategies"""
    try:
        # Try pip install with trusted hosts
        cmd = [
            sys.executable, "-m", "pip", "install", package,
            "--trusted-host", "pypi.org",
            "--trusted-host", "pypi.python.org",
            "--trusted-host", "files.pythonhosted.org",
            "--break-system-packages"
        ]
        subprocess.check_call(cmd)
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        try:
            # Try with --user flag
            cmd = [
                sys.executable, "-m", "pip", "install", package, "--user",
                "--trusted-host", "pypi.org",
                "--trusted-host", "pypi.python.org",
                "--trusted-host", "files.pythonhosted.org"
            ]
            subprocess.check_call(cmd)
            print(f"✅ Successfully installed {package} with --user")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False

def main():
    """Install all required packages"""
    required_packages = [
        "openai==1.58.1",
        "tavily-python==0.5.0",
        "pydantic-ai",
        "ag-ui-protocol"
    ]

    print("Installing dependencies for main.py...")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    failed_packages = []

    for package in required_packages:
        if not install_package(package):
            failed_packages.append(package)

    if failed_packages:
        print(f"\n❌ Failed to install: {failed_packages}")
        print("\n💡 Alternative solutions:")
        print("1. Use main_simple.py (recommended) - has all functionality")
        print("2. Try: uv pip install openai tavily-python pydantic-ai ag-ui-protocol")
        print("3. Create a virtual environment: python -m venv venv && source venv/bin/activate")
        return False
    else:
        print("\n✅ All dependencies installed successfully!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)