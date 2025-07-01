#!/usr/bin/env python3
"""
Setup script for the Modern ChatGPT Interface
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def check_env_file():
    """Check if .env file exists and prompt user to configure it"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        if env_example.exists():
            print("\n📝 Creating .env file from template...")
            try:
                with open(env_example, "r") as src, open(env_file, "w") as dst:
                    dst.write(src.read())
                print("✅ .env file created")
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return False
        else:
            print("❌ .env.example file not found")
            return False

    print("\n⚠️  IMPORTANTE: Configure sua chave da OpenAI no arquivo .env")
    print("   Abra o arquivo .env e adicione sua OPENAI_API_KEY")
    return True


def check_assistant_ids():
    """Remind user to update assistant IDs"""
    print("\n⚠️  IMPORTANTE: Atualize os IDs dos assistants OpenAI")
    print("   Edite o arquivo server/config.py e substitua:")
    print("   - asst_organizador_atas_id")
    print("   - asst_criador_propostas_id")
    print("   pelos IDs reais dos seus assistants na OpenAI")


def main():
    """Main setup function"""
    print("🚀 Configurando o ChatGPT Interface Moderno...")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Arquivo requirements.txt não encontrado")
        print("   Execute este script na pasta raiz do projeto")
        return False

    # Install requirements
    if not install_requirements():
        return False

    # Check environment file
    if not check_env_file():
        return False

    # Remind about assistant IDs
    check_assistant_ids()

    print("\n" + "=" * 50)
    print("✅ Setup concluído!")
    print("\n📋 Próximos passos:")
    print("1. Configure sua OPENAI_API_KEY no arquivo .env")
    print("2. Atualize os IDs dos assistants em server/config.py")
    print("3. Execute: python run.py")
    print("4. Acesse: http://127.0.0.1:1338")
    print("\n🎉 Divirta-se!")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
