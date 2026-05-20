#!/usr/bin/env python3
"""
upload_drive.py
===============
Faz upload dos arquivos gerados para Google Drive automaticamente.

Dependências: requests (já instalado no GitHub Actions)

Uso:
    python scripts/upload_drive.py
"""

import os
import sys
import glob
from pathlib import Path
import json
import base64

try:
    import requests
except ImportError:
    print("❌ Dependência faltando: requests")
    sys.exit(1)


def upload_file_to_drive(file_path, folder_id, access_token):
    """Faz upload de um arquivo para o Google Drive."""
    
    try:
        file_obj = Path(file_path)
        if not file_obj.exists():
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            return False
        
        # Headers com o token de acesso
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Detecta MIME type
        mime_types = {
            '.html': 'text/html',
            '.pdf': 'application/pdf',
            '.json': 'application/json'
        }
        mime_type = mime_types.get(file_obj.suffix, 'text/plain')
        
        # Metadados do arquivo
        file_metadata = {
            'name': file_obj.name,
            'parents': [folder_id]
        }
        
        # URL para upload multipart
        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
        
        # Prepara o arquivo
        with open(file_path, 'rb') as f:
            files = {
                'data': ('metadata', json.dumps(file_metadata), 'application/json'),
                'file': (file_obj.name, f, mime_type)
            }
            
            response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload: {file_obj.name}")
            print(f"   ID: {result.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Erro ao fazer upload de {file_path}")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao fazer upload de {file_path}: {e}")
        return False


def main():
    """Função principal."""
    
    print("\n" + "="*60)
    print("📤 UPLOAD PARA GOOGLE DRIVE")
    print("="*60)
    
    # Obtém credenciais do ambiente
    access_token = os.getenv('GOOGLE_DRIVE_TOKEN')
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    if not access_token:
        print("❌ Token não encontrado em GOOGLE_DRIVE_TOKEN")
        print("   Configure o secret no GitHub")
        sys.exit(1)
    
    if not folder_id:
        print("❌ Folder ID não encontrado em GOOGLE_DRIVE_FOLDER_ID")
        print("   Configure no workflow YAML")
        sys.exit(1)
    
    print(f"\n📁 Pasta destino ID: {folder_id[:20]}...")
    
    # Procura pelos arquivos gerados
    files_to_upload = glob.glob("output/briefing_*")
    
    if not files_to_upload:
        print("⚠️  Nenhum arquivo encontrado em output/")
        sys.exit(1)
    
    print(f"📂 Arquivos para upload: {len(files_to_upload)}\n")
    
    # Faz upload de cada arquivo
    success_count = 0
    for file_path in files_to_upload:
        if upload_file_to_drive(file_path, folder_id, access_token):
            success_count += 1
    
    print(f"\n✅ Upload concluído! {success_count}/{len(files_to_upload)} arquivos enviados")
    
    if success_count == len(files_to_upload):
        print("🎉 Todos os arquivos foram enviados com sucesso!")
        sys.exit(0)
    else:
        print(f"⚠️  {len(files_to_upload) - success_count} arquivo(s) falharam")
        sys.exit(1)


if __name__ == "__main__":
    main()
