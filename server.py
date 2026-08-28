import asyncio
import os
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

BASE_URL = "https://bot-pensound.fly.dev"

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
        .card { background: #1e1e1e; border-radius: 12px; padding: 20px; max-width: 400px; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        label { display: block; margin-top: 15px; text-align: left; font-weight: bold; color: #aaa; }
        input[type="text"], input[type="file"] { margin: 8px 0 15px 0; display: block; width: 100%; color: #ccc; box-sizing: border-box; }
        input[type="text"] { background: #2a2a2a; border: 1px solid #444; padding: 10px; border-radius: 6px; color: #fff; }
        button { background: #8a2be2; color: #fff; border: none; padding: 12px 20px; font-size: 16px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>PenSound Manager</h2>
        <p>Cadastrar Novo Card de Músicas</p>
        
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <label>Nome do Pacote:</label>
            <input type="text" name="package_name" placeholder="Ex: Paredão do DJ Vini" required>

            <label>1. Arquivo do Pacote (.zip):</label>
            <input type="file" name="zip_file" required>
            
            <label>2. Imagem da Capa (.jpg / .png):</label>
            <input type="file" name="cover_file" required>
            
            <button type="submit">Cadastrar no PenSound</button>
        </form>
    </div>
</body>
</html>
"""

async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def handle_upload(request):
    zip_path = None
    cover_path = None
    package_name = "Pacote sem nome"
    
    try:
        reader = await request.multipart()
        home_dir = os.path.expanduser("~")
        
        while True:
            field = await reader.next()
            if field is None:
                break
                
            if field.name == 'package_name':
                package_name = await field.text()
                
            elif field.name == 'zip_file':
                orig_filename = field.filename or "pacote.zip"
                zip_path = os.path.join(home_dir, orig_filename)
                print(f"\n📥 Recebendo pacote: {orig_filename}...")
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        
            elif field.name == 'cover_file':
                cover_path = os.path.join(home_dir, "capa_envio.jpg")
                print(f"📥 Recebendo capa...")
                with open(cover_path, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        if not zip_path or not cover_path:
            return web.Response(text="<h1>Erro: Envie todos os dados!</h1>", content_type='text/html')

        print(f"📤 Enviando '{package_name}' para o Telegram...")
        sent_zip_msg = await app.send_document(
            chat_id=CANAL_ID, 
            document=zip_path, 
            caption=f"📦 Pacote: {package_name}"
        )
        if os.path.exists(zip_path):
            os.remove(zip_path)

        print("🖼️ Enviando imagem da capa para o Telegram...")
        sent_cover_msg = await app.send_document(
            chat_id=CANAL_ID, 
            document=cover_path,
            caption=f"🖼️ Capa: {package_name}"
        )
        if os.path.exists(cover_path):
            os.remove(cover_path)

        zip_url = f"{BASE_URL}/stream/{CANAL_ID}/{sent_zip_msg.id}"
        cover_url = f"{BASE_URL}/stream/{CANAL_ID}/{sent_cover_msg.id}"
        
        print(f"✅ Cadastrado com sucesso: {package_name}\n")

        response_html = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resultado do Upload</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 20px; text-align: center; }}
                .card {{ background: #1e1e1e; border-radius: 12px; padding: 20px; max-width: 450px; margin: 0 auto; word-break: break-all; }}
                a {{ color: #00ffcc; text-decoration: underline; }}
                .btn-back {{ display: inline-block; margin-top: 15px; padding: 10px 15px; background: #8a2be2; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2 style="color: #00ff00;">✅ Card Cadastrado!</h2>
                <p><strong>Nome:</strong> {package_name}</p>
                <p><strong>Link do Pacote (.zip):</strong><br><a href="{zip_url}" target="_blank">{zip_url}</a></p>
                <p><strong>Link da Capa (Imagem):</strong><br><a href="{cover_url}" target="_blank">{cover_url}</a></p>
                <br>
                <a href="/" class="btn-back">⬅ Cadastrar Outro Pacote</a>
            </div>
        </body>
        </html>
        """
        return web.Response(text=response_html, content_type='text/html')

    except Exception as e:
        print(f"❌ Erro de upload: {str(e)}")
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)
        if cover_path and os.path.exists(cover_path):
            os.remove(cover_path)
        return web.Response(text=f"<h1>Erro no servidor: {str(e)}</h1>", content_type='text/html', status=500)

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
        else:
            file_size = getattr(file_obj, 'file_size', 0)
            file_name = getattr(file_obj, 'file_name', 'pacote.zip')

        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{file_name}"',
                'Content-Length': str(file_size)
            }
        )
        await response.prepare(request)
        
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
                package_name = msg.caption.replace("📦 Pacote:", "").strip()
                pacotes.append({
                    "id": msg.id,
                    "nome": package_name,
                    "zip_url": f"{BASE_URL}/stream/{CANAL_ID}/{msg.id}",
                    "cover_url": f"{BASE_URL}/stream/{CANAL_ID}/{msg.id + 1}"
                })
        return web.json_response(pacotes)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def main():
    await app.start()
    
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
    print("\n🚀 Servidor PenSound Nativo Rodando na porta 8080!\n")
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    loop.run_until_complete(main())
