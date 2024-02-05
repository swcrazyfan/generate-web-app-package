import streamlit as st
import os
import subprocess
import tempfile
import shutil

# Streamlit UI
st.title('HTML to Desktop App Generator')

# Text area for user to paste HTML
user_html = st.text_area("Paste your HTML code here:", height=300)

# Button to generate the app
if st.button('Generate App'):
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Save the HTML to a file
        html_path = os.path.join(tmpdirname, 'index.html')
        with open(html_path, 'w') as f:
            f.write(user_html)

        # Generate Flask app to serve the HTML
        flask_app_py = os.path.join(tmpdirname, 'flask_app.py')
        with open(flask_app_py, 'w') as f:
            f.write("""
from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='static')

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
""")

        # Generate pywebview script
        pywebview_script = os.path.join(tmpdirname, 'webview_app.py')
        with open(pywebview_script, 'w') as f:
            f.write("""
import webview
import threading
import subprocess
import os

def run_flask():
    subprocess.run(['python', 'flask_app.py'], cwd=os.path.abspath('.'))

if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.start()

    webview.create_window('Your HTML App', 'http://localhost:5000')
    t.join()
""")

        # Generate PyInstaller spec file for macOS app
        spec_path = os.path.join(tmpdirname, 'app.spec')
        with open(spec_path, 'w') as f:
            f.write(f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['webview_app.py'],
             pathex=['{tmpdirname}'],
             binaries=[],
             datas=[('{html_path}', '.'), ('{flask_app_py}', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='app')
app = BUNDLE(coll,
             name='app.app',
             icon=None,
             bundle_identifier=None)
""")

        # Run PyInstaller
        try:
            subprocess.run(['pyinstaller', spec_path, '--onefile'], cwd=tmpdirname, check=True)
            st.success('App generated successfully.')
            # Provide download link for macOS app
            app_path = os.path.join(tmpdirname, 'dist', 'app.app')
            if os.path.exists(app_path):
                shutil.move(app_path, os.getcwd())
                st.markdown(f'Download your app: [app.app](app.app)')
            else:
                st.error('Failed to generate macOS app.')
        except subprocess.CalledProcessError as e:
            st.error(f'Error during app generation: {e}')
