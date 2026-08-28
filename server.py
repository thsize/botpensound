import asyncio
import os
import mimetypes
from aiohttp import web
import aiohttp_cors

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client

API_ID = 31285889
API_HASH = "48fec694d07f2a32566dfe17b66a0d7a"
CANAL_ID = -1003997037273

BASE_URL = "https://bot-pensound.onrender.com"

app = Client("pensound_user", api_id=API_ID, api_hash=API_HASH)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PenSound Manager</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 20px; text-align: center; }
        .card { background: #1e1e1e; border-radius: 12px; padding: 20px; max-width: 420px; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        label { display: block; margin-top: 15px; text-align: left; font-weight: bold; color: #aaa; }
        input[type="text"], input[type="file"], select { margin: 8px 0 15px 0; display: block; width: 100%; color: #ccc; box-sizing: border-box; }
        input[type="text"], select { background: #2a2a2a; border: 1px solid #444; padding: 10px; border-radius: 6px; color: #fff; }
        button { background: #8a2be2; color: #fff; border: none; padding: 12px 20px; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 15px; }
        button:disabled { background: #555; cursor: not-allowed; }
        
        .progress-container { display: none; margin-top: 20px; text-align: left; }
        .progress-bar-bg { background: #333; border-radius: 8px; height: 18px; width: 100%; overflow: hidden; margin-top: 5px; }
        .progress-bar-fill { background: #00ffcc; height: 100%; width: 0%; transition: width 0.2s; }
        .status-text { font-size: 13px; color: #00ffcc; margin-top: 8px; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>PenSound Manager</h2>
        <p>Cadastrar Novo Card de Músicas</p>
        
        <form id="uploadForm">
            <label>Nome do Pacote:</label>
            <input type="text" id="package_name" required placeholder="Ex: Paredão do DJ Vini">

            <label>Categoria:</label>
            <select id="category" required>
                <option value="PAGODÃO">Pagodão</option>
                <option value="REPERTÓRIO">Repertório</option>
                <option value="ARROCHA">Arrocha</option>
                <option value="AFRO HOUSE">Afro House</option>
                <option value="HARD TECHNO">Hard Techno</option>
                <option value="PHONK">Phonk</option>
                <option value="TRAP">Trap</option>
                <option value="OUTROS">Outros</option>
            </select>

            <label>1. Arquivo do Pacote (.zip):</label>
            <input type="file" id="zip_file" accept=".zip" required>
            
            <label>2. Imagem da Capa (.jpg / .png):</label>
            <input type="file" id="cover_file" accept="image/*" required>
            
            <button type="submit" id="btnSubmit">Cadastrar no PenSound</button>
        </form>

        <div class="progress-container" id="progressArea">
            <label id="progressLabel">Enviando arquivo: 0%</label>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progressBar"></div>
            </div>
            <div class="status-text" id="statusText">Iniciando upload...</div>
        </div>
    </div>

    <script>
        const form = document.getElementById('uploadForm');
        const progressArea = document.getElementById('progressArea');
        const progressBar = document.getElementById('progressBar');
        const progressLabel = document.getElementById('progressLabel');
        const statusText = document.getElementById('statusText');
        const btnSubmit = document.getElementById('btnSubmit');

        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData();
            formData.append('package_name', document.getElementById('package_name').value);
            formData.append('category', document.getElementById('category').value);
            formData.append('zip_file', document.getElementById('zip_file').files[0]);
            formData.append('cover_file', document.getElementById('cover_file').files[0]);

            btnSubmit.disabled = true;
            progressArea.style.display = 'block';

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);

            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                    progressLabel.innerText = 'Enviando do PC/Celular: ' + percent + '%';
                    if (percent === 100) {
                        statusText.innerText = '⚙️ Processando e registrando no Telegram... Aguarde!';
                    }
                }
            };

            xhr.onload = function() {
                if (xhr.status === 200) {
                    statusText.innerText = '✅ Card cadastrado com sucesso!';
                    alert('Pacote enviado e cadastrado com sucesso!');
                    window.location.reload();
                } else {
                    statusText.innerText = '❌ Erro no envio!';
                    alert('Erro no servidor ao enviar arquivo.');
                    btnSubmit.disabled = false;
                }
            };

            xhr.onerror = function() {
                statusText.innerText = '❌ Erro na conexão!';
                alert('Falha na rede durante o upload.');
                btnSubmit.disabled = false;
            };

            xhr.send(formData);
        });
    </script>
</body>
</html>
"""

async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def handle_upload(request):
    zip_path = None
    cover_path = None
    package_name = "Pacote sem nome"
    category = "OUTROS"
    
    try:
        reader = await request.multipart()
        home_dir = os.path.expanduser("~")
        
        while True:
            field = await reader.next()
            if field is None:
                break
                
            if field.name == 'package_name':
                package_name = await field.text()

            elif field.name == 'category':
                category = await field.text()
                
            elif field.name == 'zip_file':
                orig_filename = field.filename or "pacote.zip"
                zip_path = os.path.join(home_dir, orig_filename)
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk(1024 * 1024 * 2)
                        if not chunk:
                            break
                        f.write(chunk)
                        
            elif field.name == 'cover_file':
                orig_filename = field.filename or "capa.jpg"
                cover_path = os.path.join(home_dir, f"capa_{orig_filename}")
                with open(cover_path, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        if not zip_path or not cover_path:
            return web.Response(text="Erro: Envie todos os dados!", status=400)

        sent_zip_msg = await app.send_document(
            chat_id=CANAL_ID, 
            document=zip_path, 
            caption=f"📦 Pacote: {package_name} | Categoria: {category}"
        )
        if os.path.exists(zip_path):
            os.remove(zip_path)

        sent_cover_msg = await app.send_document(
            chat_id=CANAL_ID, 
            document=cover_path,
            caption=f"🖼️ Capa: {package_name}"
        )
        if os.path.exists(cover_path):
            os.remove(cover_path)

        return web.Response(text="OK", status=200)

    except Exception as e:
        print(f"❌ Erro de upload: {str(e)}")
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)
        if cover_path and os.path.exists(cover_path):
            os.remove(cover_path)
        return web.Response(text=str(e), status=500)

async def handle_download(request):
    try:
        chat_id = int(request.match_info.get('chat_id'))
        message_id = int(request.match_info.get('message_id'))
        
        msg = await app.get_messages(chat_id, message_id)
        
        if not msg or not msg.media:
            return web.Response(status=404, text="Arquivo nao encontrado")
            
        file_obj = msg.document or msg.photo or msg.audio or msg.video
        
        if msg.photo:
            file_size = msg.photo.file_size
            file_name = "capa.jpg"
            disposition = "inline"
            content_type = "image/jpeg"
        else:
            file_size = getattr(file_obj, 'file_size', 0)
            file_name = getattr(file_obj, 'file_name', 'pacote.zip')
            disposition = f'attachment; filename="{file_name}"'
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = 'application/zip' if file_name.endswith('.zip') else 'application/octet-stream'

        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': content_type,
                'Content-Disposition': disposition,
                'Content-Length': str(file_size)
            }
        )
        await response.prepare(request)
        
        # Faz o streaming direto do Telegram pro App Android
        async for chunk in app.stream_media(msg):
            await response.write(chunk)
            
        return response
    except Exception as e:
        return web.Response(status=500, text=str(e))

async def handle_api_pacotes(request):
    pacotes = []
    try:
        async for msg in app.get_chat_history(CANAL_ID, limit=50):
            if msg.caption and "📦 Pacote:" in msg.caption:
                caption = msg.caption
                package_name = caption.split("📦 Pacote:")[1].split("|")[0].strip()
                
                categoria = "OUTROS"
                if "Categoria:" in caption:
                    categoria = caption.split("Categoria:")[1].strip().upper()

                pacotes.append({
                    "id": msg.id,
                    "nome": package_name,
                    "categoria": categoria,
                    "zip_url": f"{BASE_URL}/stream/{CANAL_ID}/{msg.id}",
                    "cover_url": f"{BASE_URL}/stream/{CANAL_ID}/{msg.id + 1}"
                })
        return web.json_response(pacotes)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def main():
    await app.start()
    
    # Define limite de payload e timeouts altos para streaming longo
    server = web.Application(client_max_size=1024 * 1024 * 1024 * 10)
    
    cors = aiohttp_cors.setup(server, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    resource_index = server.router.add_resource('/')
    route_index = resource_index.add_route('GET', handle_index)
    cors.add(route_index)
    
    resource_upload = server.router.add_resource('/upload')
    route_upload = resource_upload.add_route('POST', handle_upload)
    cors.add(route_upload)

    resource_stream = server.router.add_resource('/stream/{chat_id}/{message_id}')
    route_stream = resource_stream.add_route('GET', handle_download)
    cors.add(route_stream)

    resource_api = server.router.add_resource('/api/pacotes')
    route_api = resource_api.add_route('GET', handle_api_pacotes)
    cors.add(route_api)

    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    print("\n🚀 Servidor PenSound com Streaming Corrigido Rodando!\n")
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    loop.run_until_complete(main())
