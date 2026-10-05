import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
modelo_ia = genai.GenerativeModel("gemini-3.8-flash")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Histórico simples de conversa por canal
historico = {}


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


# ---------- COMANDOS DE MODERAÇÃO ----------

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    await membro.ban(reason=motivo)
    await ctx.send(f"🔨 {membro} foi banido. Motivo: {motivo}")


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, membro: discord.Member, *, motivo="Sem motivo"):
    await membro.kick(reason=motivo)
    await ctx.send(f"👢 {membro} foi expulso. Motivo: {motivo}")


@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, membro: discord.Member, minutos: int, *, motivo="Sem motivo"):
    from datetime import timedelta
    await membro.timeout(timedelta(minutes=minutos), reason=motivo)
    await ctx.send(f"🔇 {membro} foi silenciado por {minutos} minuto(s).")


@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, membro: discord.Member):
    await membro.timeout(None)
    await ctx.send(f"🔊 {membro} pode falar novamente.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, quantidade: int):
    await ctx.channel.purge(limit=quantidade + 1)
    await ctx.send(f"🧹 {quantidade} mensagem(ns) apagada(s).", delete_after=5)


# ---------- GERAÇÃO DE IMAGEM ----------

@bot.command()
async def imagem(ctx, *, descricao):
    await ctx.send("🎨 Gerando imagem, aguarde...")
    try:
        from google import genai as genai_novo
        from google.genai import types
        import io
        cliente = genai_novo.Client(api_key=GEMINI_API_KEY)
        r = cliente.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=descricao,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        for part in r.candidates[0].content.parts:
            if part.inline_data:
                arquivo = discord.File(io.BytesIO(part.inline_data.data), filename="imagem.png")
                await ctx.send(file=arquivo)
                return
        await ctx.send("A IA não gerou uma imagem dessa vez, tente descrever de outra forma.")
    except Exception as e:
        await ctx.send(f"Erro ao gerar imagem: {e}")


# ---------- MÚSICA ----------

import asyncio
import discord
import yt_dlp

YDL_OPTS = {"format": "bestaudio/best", "noplaylist": True, "quiet": True}
FFMPEG_OPTS = {"options": "-vn"}
fila = {}


@bot.command()
async def entrar(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("🎶 Entrei na call!")
    else:
        await ctx.send("Você precisa estar em uma call.")


@bot.command()
async def tocar(ctx, *, busca):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("Entre em uma call primeiro.")
    await ctx.send(f"🔎 Procurando: {busca}")
    try:
        info = await asyncio.get_event_loop().run_in_executor(None, lambda: yt_dlp.YoutubeDL(YDL_OPTS).extract_info(f"ytsearch:{busca}", download=False)["entries"][0])
        url = info["url"]
        titulo = info.get("title", "música")
        if os.name == "nt":
            ffmpeg_path = r"C:\Users\MM47\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
        else:
            ffmpeg_path = "ffmpeg"
        ctx.voice_client.play(discord.FFmpegOpusAudio(url, **FFMPEG_OPTS, executable=ffmpeg_path))
        await ctx.send(f"▶️ Tocando: **{titulo}**")
    except Exception as e:
        await ctx.send(f"Erro ao tocar: {e}")


@bot.command()
async def parar(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏹️ Parado.")


@bot.command()
async def sair(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Saindo da call.")


# ---------- CHAT COM IA ----------

@bot.command()
async def ask(ctx, *, pergunta):
    await ctx.send(gpt_resposta(ctx.channel.id, pergunta)[:2000])


def gpt_resposta(canal_id, texto):
    try:
        chat = historico.get(canal_id)
        if chat is None:
            chat = modelo_ia.start_chat(history=[
                {"role": "user", "parts": ["Você se chama Fernando e é um amigo do usuário. Responda de forma direta, objetiva e sem brincadeiras. Sem piadas, sem emojis, sem enrolação."]},
                {"role": "model", "parts": ["Entendido. Sou o Fernando e vou responder de forma direta e objetiva."]},
            ])
            historico[canal_id] = chat
        resposta = chat.send_message(texto)
        return resposta.text
    except Exception as e:
        return f"Erro ao falar com a IA: {e}"


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Se mencionarem o bot, responde com IA
    if bot.user in message.mentions:
        pergunta = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if pergunta:
            await message.channel.send(gpt_resposta(message.channel.id, pergunta)[:2000])
    # Se a mensagem mencionar "fernando", responde com IA
    elif "fernando" in message.content.lower():
        pergunta = message.content
        if pergunta.strip():
            await message.channel.send(gpt_resposta(message.channel.id, pergunta)[:2000])
    await bot.process_commands(message)


@bot.command()
async def limparmemoria(ctx):
    historico.pop(ctx.channel.id, None)
    await ctx.send("🧠 Memória da conversa apagada.")


@bot.command()
async def ajuda(ctx):
    texto = """**Comandos disponíveis:**
`!ask <pergunta>` — pergunta para a IA
`!imagem <descrição>` — gera uma imagem com IA
`!ban @user [motivo]` — bane
`!kick @user [motivo]` — expulsa
`!mute @user <minutos>` — silencia
`!unmute @user` — dessilencia
`!clear <n>` — apaga mensagens
`!limparmemoria` — limpa a memória da IA
Mencione o bot (@) para conversar com a IA direto."""
    await ctx.send(texto)


bot.run(DISCORD_TOKEN)
