# Yêu cầu: `pip install streamlit google-api-python-client google-auth-httplib2 google-auth-oauthlib`

import streamlit as st
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account

# === Thiết lập OAuth 2.0 ===
SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/documents.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Tạo từ Google Cloud Console

def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    return drive_service, docs_service

# === Hàm xử lý văn bản Google Docs ===
def extract_gpa_from_doc(doc_content):
    text = ""
    for element in doc_content.get('body').get('content', []):
        if 'paragraph' in element:
            for run in element['paragraph'].get('elements', []):
                text += run.get('textRun', {}).get('content', '')
    
    match = re.search(r"1\.4.*?([0-4]\.[0-9]{2})", text, re.DOTALL)
    return float(match.group(1)) if match else None

# === Giao diện Web ===
st.title("📄 Bot Trích Xuất GPA từ DRL")

drive_link = st.text_input("🔗 Nhập link thư mục Google Drive chứa các folder sinh viên:")

if drive_link:
    folder_id_match = re.search(r"folders/([\w-]+)", drive_link)
    if not folder_id_match:
        st.error("❌ Link không hợp lệ. Hãy nhập đúng link thư mục Drive.")
    else:
        folder_id = folder_id_match.group(1)
        drive_service, docs_service = get_service()

        results = drive_service.files().list(q=f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'",
                                            pageSize=100, fields="files(id, name)").execute()
        folders = results.get('files', [])

        data = []

        for folder in folders:
            folder_name = folder['name']
            folder_id = folder['id']

            files = drive_service.files().list(q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
                                              fields="files(id, name)").execute().get('files', [])

            target_file = next((f for f in files if 'phiếu chấm' in f['name'].lower()), None)
            if target_file:
                doc = docs_service.documents().get(documentId=target_file['id']).execute()
                gpa = extract_gpa_from_doc(doc)
                if gpa:
                    data.append((folder_name, gpa))

        if data:
            st.success("✅ Đã trích xuất xong!")
            st.table({"Tên sinh viên": [x[0] for x in data], "GPA": [x[1] for x in data]})
        else:
            st.warning("⚠️ Không tìm được file phù hợp hoặc không có GPA.")
