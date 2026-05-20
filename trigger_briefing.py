#!/usr/bin/env python3
"""
trigger_briefing.py
===================
Dispara o workflow GitHub Actions para gerar briefing diário.
O workflow faz web search, JSON, HTML/PDF e upload ao Google Drive.

Uso:
    python trigger_briefing.py
"""

import subprocess
import sys
from datetime import datetime

def trigger_github_workflow():
    """
    Dispara o workflow 'briefing-diario.yml' via GitHub CLI.
    Requer: gh cli instalado e autenticado
    """
    print("=" * 60)
    print("🚀 Disparando GitHub Actions Workflow")
    print("=" * 60)
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Dispara o workflow
        result = subprocess.run([
            "gh", "workflow", "run", "briefing-diario.yml",
            "-f", f"data={data_hoje}"
        ], check=True, capture_output=True, text=True)
        
        print(f"\n✅ Workflow disparado com sucesso!")
        print(f"📅 Data: {data_hoje}")
        print(f"⏱️  Tempo estimado: 2-3 minutos")
        print(f"\n📊 O que vai acontecer:")
        print("  1. Web search (Fed, Trump, Cripto, B3)")
        print("  2. Gera JSON com dados reais")
        print("  3. Renderiza HTML com gráficos SVG")
        print("  4. Gera PDF via WeasyPrint")
        print("  5. Upload automático ao Google Drive")
        print(f"\n📁 Google Drive: /Meu Drive/Briefing Diário/")
        print(f"   └─ briefing_{data_hoje.replace('-','')}.html")
        print(f"   └─ briefing_{data_hoje.replace('-','')}.pdf")
        
        print(f"\n🔗 Acompanhe em: https://github.com/<seu-user>/briefing-automation/actions")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao disparar workflow:")
        print(f"   {e.stderr}")
        print(f"\n💡 Verifique:")
        print("   1. GitHub CLI instalado: gh --version")
        print("   2. Autenticado: gh auth status")
        print("   3. Workflow existe: .github/workflows/briefing-diario.yml")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ GitHub CLI não encontrado")
        print(f"\n💡 Instale com:")
        print("   Windows: choco install gh")
        print("   macOS: brew install gh")
        print("   Linux: sudo apt install gh")
        sys.exit(1)

if __name__ == "__main__":
    trigger_github_workflow()
