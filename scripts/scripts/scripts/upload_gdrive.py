#!/usr/bin/env python3
"""
upload_gdrive.py
================
Faz upload de HTML/PDF/JSON ao Google Drive via service account.

Uso:
    python upload_gdrive.py \
      --folder-id "PASTA_ID" \
      --json-file "briefing_*.json" \
      --html-file "briefing_*.html" \
      --pdf-file "briefing_*.pdf"
"""

import argparse
import glob
import sys
from pathlib import Path
from datetime import date

try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("❌ Dependências Google faltando. Instale com:")
    print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)


SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_gdrive_service():
    """Autentica e retorna o serviço Google Drive."""
    try:
        # Credenciais vêm da variável de ambiente GOOGLE_APPLICATION_CREDENTIALS
        # configurada pelo GitHub Actions
        credentials = Credentials.from_service_account_file(
            filename=None,  # Usa variável de ambiente
            scopes=SCOPES
        )
        
        # Ou ler do arquivo se não estiver em CI/CD
        creds_file = Path("credentials.json")
        if creds_file.exists():
            credentials = Credentials.from_service_account_file(
                filename=str(creds_file),
                scopes=SCOPES
            )
        
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Erro ao autenticar no Google Drive: {e}")
        print(f"\n💡 Configure as credenciais:")
        print("   1. Crie um Service Account no Google Cloud Console")
        print("   2. Salve JSON em 'credentials.json'")
        print("   3. Ou defina GOOGLE_APPLICATION_CREDENTIALS")
        sys.exit(1)


def upload_file(service, file_path, folder_id, mime_type="text/plain"):
    """Faz upload de um arquivo para o Google Drive."""
    try:
        file_obj = Path(file_path)
        if not file_obj.exists():
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            return None
        
        file_metadata = {
            'name': file_obj.name,
            'parents': [folder_id]
        }
        
        # Detecta MIME type
        if file_path.endswith('.html'):
            mime_type = 'text/html'
        elif file_path.endswith('.pdf'):
            mime_type = 'application/pdf'
        elif file_path.endswith('.json'):
            mime_type = 'application/json'
        
        media = MediaFileUpload(file_path, mimetype=mime_type)
        
        # Delete arquivo antigo se existir (mesmo nome)
        query = f"name='{file_obj.name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', pageSize=1, fields='files(id)').execute()
        for existing_file in results.get('files', []):
            service.files().delete(fileId=existing_file['id']).execute()
            print(f"  Removido arquivo anterior: {file_obj.name}")
        
        # Upload novo
        file_resp = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"✅ Upload: {file_obj.name}")
        print(f"   Link: {file_resp.get('webViewLink', 'N/A')}")
        
        return file_resp
    except Exception as e:
        print(f"❌ Erro ao fazer upload de {file_path}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Upload de briefing ao Google Drive")
    parser.add_argument("--folder-id", required=True, help="ID da pasta no Google Drive")
    parser.add_argument("--json-file", help="Padrão do arquivo JSON (ex: briefing_*.json)")
    parser.add_argument("--html-file", help="Padrão do arquivo HTML")
    parser.add_argument("--pdf-file", help="Padrão do arquivo PDF")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("📤 UPLOAD PARA GOOGLE DRIVE")
    print("="*60)
    
    service = get_gdrive_service()
    
    files_to_upload = []
    
    # Resolve globs
    if args.json_file:
        files_to_upload.extend(glob.glob(args.json_file))
    if args.html_file:
        files_to_upload.extend(glob.glob(args.html_file))
    if args.pdf_file:
        files_to_upload.extend(glob.glob(args.pdf_file))
    
    if not files_to_upload:
        print("⚠️  Nenhum arquivo encontrado para upload")
        sys.exit(1)
    
    print(f"\n📁 Pasta destino: {args.folder_id}")
    print(f"📂 Arquivos para upload: {len(files_to_upload)}\n")
    
    for file_path in files_to_upload:
        upload_file(service, file_path, args.folder_id)
    
    print(f"\n✅ Upload concluído!")
    print(f"   Acesse: https://drive.google.com/drive/folders/{args.folder_id}")


if __name__ == "__main__":
    main()
