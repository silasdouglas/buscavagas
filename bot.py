import asyncio
import logging
import time
import random
from urllib.parse import urlparse, parse_qs
from telegram import Bot
from telegram.error import RetryAfter
from supabase import create_client, Client
import unicodedata

import config
import scraping

# --- Configuração de Logs ---
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Conexão Supabase ---
supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# -----------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -----------------------------------------------------------------
def normalizar_texto(texto: str) -> str:
    """Remove acentos e coloca em minúsculo para comparação."""
    if not texto: return ""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()

def verificar_modalidade(texto_local: str, modalidades_aceitas: list) -> bool:
    """Filtra Remoto, Híbrido ou Presencial."""
    if not modalidades_aceitas: return True 
    texto = normalizar_texto(texto_local)
    eh_remoto = "home office" in texto or "remoto" in texto
    eh_hibrido = "hibrido" in texto or "hybrid" in texto
    eh_presencial = not eh_remoto and not eh_hibrido
    
    if "remoto" in modalidades_aceitas and eh_remoto: return True
    if "hibrido" in modalidades_aceitas and eh_hibrido: return True
    if "presencial" in modalidades_aceitas and eh_presencial: return True
    return False

def extrair_id_unico(vaga: dict) -> str:
    """Gera um ID único dependendo da fonte."""
    link = vaga.get('link', '')
    
    # 1. Tenta pegar o JK do Indeed
    try:
        parsed = urlparse(link)
        jk = parse_qs(parsed.query).get('jk', [None])[0]
        if jk: return jk
    except: pass
    
    # 2. Se não tiver JK (ex: QConcursos), usa parte do link
    if link:
        return link[-30:]
    
    return None

# -----------------------------------------------------------------
# FUNÇÕES DE BANCO DE DADOS
# -----------------------------------------------------------------
def obter_ids_ja_salvos(lista_de_ids: list) -> set:
    if not lista_de_ids: return set()
    try:
        response = supabase.table("vagas").select("jk_code").in_("jk_code", lista_de_ids).execute()
        return {item['jk_code'] for item in response.data}
    except Exception as e:
        logger.error(f"Erro ao consultar banco: {e}")
        return set()

def salvar_vaga(id_unico: str, titulo: str) -> None:
    try:
        data = {"jk_code": id_unico, "titulo_vaga": titulo}
        supabase.table("vagas").insert(data).execute()
    except Exception as e:
        logger.error(f"Erro ao salvar vaga {id_unico}: {e}")

# -----------------------------------------------------------------
# ENVIO TELEGRAM
# -----------------------------------------------------------------
async def enviar_telegram(bot, chat_id, topic_id, mensagem):
    try:
        await bot.send_message(
            chat_id=chat_id,
            message_thread_id=topic_id,
            text=mensagem,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        return True
    except RetryAfter as e:
        logger.warning(f"⏳ Telegram pediu pausa de {e.retry_after}s.")
        await asyncio.sleep(e.retry_after)
        return await enviar_telegram(bot, chat_id, topic_id, mensagem)
    except Exception as e:
        logger.error(f"Erro ao enviar Telegram: {e}")
        return False

# -----------------------------------------------------------------
# LOOP PRINCIPAL
# -----------------------------------------------------------------
async def main():
    inicio_total = time.time()
    logger.info("🤖 Iniciando Bot V7 (Visual Limpo)...")
    
    bot = Bot(token=config.BOT_TOKEN)

    # Mistura as buscas para variar o padrão
    lista_buscas = config.BUSCAS.copy()
    random.shuffle(lista_buscas)

    for item_busca in lista_buscas:
        termo = item_busca['termo']
        id_topico = item_busca['topic_id']
        fonte = item_busca.get('fonte', 'indeed')
        
        termos_obrigatorios = item_busca.get('obrigatorio', [])
        bloqueios = config.PALAVRAS_BLOQUEADAS + item_busca.get('bloqueado', [])
        modalidades = item_busca.get('modalidades', [])
        
        vagas_brutas = []

        # --- SELETOR DE FONTE ---
        if fonte == 'qconcursos':
            vagas_brutas = scraping.buscar_qconcursos()
            
        elif fonte == 'indeed':
            locais = item_busca.get('locais', [""])
            locais_random = locais.copy()
            random.shuffle(locais_random)
            
            for local in locais_random:
                res = scraping.buscar_vagas_indeed(termo, local)
                vagas_brutas.extend(res)
                if not res: await asyncio.sleep(random.uniform(2, 4))
        
        if not vagas_brutas:
            continue

        # --- DEDUPLICAÇÃO E FILTROS ---
        ids_para_checar = []
        mapa_vagas = {}
        
        for v in vagas_brutas:
            uid = extrair_id_unico(v)
            if uid:
                ids_para_checar.append(uid)
                mapa_vagas[uid] = v
        
        ids_existentes = obter_ids_ja_salvos(ids_para_checar)
        novas_enviadas = 0

        for uid in ids_para_checar:
            if uid in ids_existentes: continue 
            
            vaga = mapa_vagas[uid]
            titulo_norm = normalizar_texto(vaga['titulo'])
            
            # Filtros de Texto
            if any(normalizar_texto(p) in titulo_norm for p in bloqueios): continue
            
            if termos_obrigatorios:
                texto_check = titulo_norm
                if fonte == 'qconcursos':
                    texto_check += normalizar_texto(vaga.get('resumo_q', ''))
                
                if not any(normalizar_texto(o) in texto_check for o in termos_obrigatorios):
                    continue
            
            # Filtros de Local/Modalidade (Apenas Indeed)
            if fonte == 'indeed':
                if not verificar_modalidade(vaga.get('local', ''), modalidades): continue
                locais_config = item_busca.get('locais', [])
                if locais_config:
                    local_norm = normalizar_texto(vaga.get('local', ''))
                    if not any(normalizar_texto(l) in local_norm for l in locais_config):
                        continue

            # --- MONTAGEM DA MENSAGEM (VISUAL LIMPO) ---
            if fonte == 'qconcursos':
                mensagem = (
                    f"🏛️ <b>CONCURSO (PE)</b>\n"
                    f"📜 <b>{vaga['titulo']}</b>\n"
                    f"ℹ️ {vaga.get('resumo_q', '')}\n\n"
                    f"<a href='{vaga['link']}'>➡️ Ver no QConcursos</a>"
                )
            else:
                # REMOVIDA A LINHA DO ID AQUI
                mensagem = (
                    f"<b>💼 {vaga['titulo']}</b>\n"
                    f"🏢 <b>Empresa:</b> {vaga['empresa']}\n"
                    f"📍 <b>Local:</b> {vaga['local']}\n"
                    f"💰 <b>Salário:</b> {vaga['salario']}\n"
                    f"📅 <b>Data:</b> {vaga.get('data_pub', 'Recente')}\n\n"
                    f"<a href='{vaga['link']}'>➡️ Ver Vaga no Indeed</a>"
                )

            # Envia e Salva
            enviou = await enviar_telegram(bot, config.CHAT_ID, id_topico, mensagem)
            if enviou:
                salvar_vaga(uid, vaga['titulo'])
                novas_enviadas += 1
                await asyncio.sleep(1) 
        
        logger.info(f"Categoria '{termo}' finalizada. {novas_enviadas} enviadas.")
        await asyncio.sleep(5) 

    tempo_total = time.time() - inicio_total
    logger.info(f"✅ Ciclo concluído em {int(tempo_total)} segundos.")

if __name__ == "__main__":
    asyncio.run(main())