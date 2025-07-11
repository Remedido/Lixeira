import discord
from discord.ext import commands, tasks
from datetime import datetime
import os

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# IDs fornecidos
CANAIS_BACKUP_DESTINO = [
    1392589268639289516,
    1392589234610766045
]
CANAL_ORIGEM_ID = 1280314639867056160
CANAIS_ENQUETE = [
    1280314639867056163,
    1383199009245626448
]
NOME_CANAL_LIXEIRA = "lixeira"
CARGO_BACKUPER = "backuper"

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")
    tarefa_do_dia_9.start()

def somente_backuper():
    async def predicate(ctx):
        return any(role.name == CARGO_BACKUPER for role in ctx.author.roles)
    return commands.check(predicate)

@bot.command()
@somente_backuper()
async def backup(ctx):
    await fazer_backup(ctx.guild)

@bot.command()
@somente_backuper()
async def apagar(ctx, quantidade: int = 100):
    if quantidade <= 0:
        await ctx.send("❌ Número inválido.")
        return
    await ctx.channel.purge(limit=quantidade + 1)
    confirm = await ctx.send(f"🗑️ {quantidade} mensagens apagadas.")
    await confirm.delete(delay=5)

async def fazer_backup(guild):
    canal_origem = guild.get_channel(CANAL_ORIGEM_ID)
    if not canal_origem:
        print("❌ Canal de origem não encontrado.")
        return

    mensagens = []
    async for msg in canal_origem.history(limit=None, oldest_first=True):
        autor = msg.author.display_name
        conteudo = msg.content
        mensagens.append(f"**{autor}**: {conteudo}")

    for destino_id in CANAIS_BACKUP_DESTINO:
        canal_backup = bot.get_channel(destino_id)
        if canal_backup:
            for i in range(0, len(mensagens), 50):
                trecho = "\n".join(mensagens[i:i+50])
                if len(trecho) > 2000:
                    partes = [trecho[j:j+2000] for j in range(0, len(trecho), 2000)]
                    for parte in partes:
                        await canal_backup.send(parte)
                else:
                    await canal_backup.send(trecho)

            print(f"✅ Backup enviado para {canal_backup.name}")
        else:
            print(f"⚠️ Canal de backup {destino_id} não encontrado.")

    await canal_origem.purge(limit=None)
    print("🧹 Mensagens apagadas após backup.")

@tasks.loop(hours=24)
async def tarefa_do_dia_9():
    hoje = datetime.now()
    if hoje.day != 9:
        return

    for guild in bot.guilds:
        canal_lixeira = discord.utils.get(guild.text_channels, name=NOME_CANAL_LIXEIRA)
        if not canal_lixeira:
            print(f"❌ Canal 'lixeira' não encontrado em {guild.name}")
            continue

        canais_mencionados = []
        for i, canal_id in enumerate(CANAIS_ENQUETE):
            canal = guild.get_channel(canal_id)
            if canal:
                canais_mencionados.append(f"{i+1}. {canal.mention}")
            else:
                canais_mencionados.append(f"{i+1}. *(Canal ID {canal_id} não encontrado)*")

        mensagem = await canal_lixeira.send(
            "📊 **Qual canal deve ser apagado hoje (dia 9)?**\n\n"
            + "\n".join(canais_mencionados) +
            "\n\nReaja com o número correspondente para votar!"
        )

        emojis_numeros = ["1️⃣", "2️⃣"]
        for emoji in emojis_numeros[:len(CANAIS_ENQUETE)]:
            await mensagem.add_reaction(emoji)

        await fazer_backup(guild)

# 🛡️ Token seguro com variável de ambiente
bot.run(os.getenv("DISCORD_TOKEN"))

