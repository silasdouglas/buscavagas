# scraping.py
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import logging
import random
from urllib.parse import quote 

def get_driver():
    options = uc.ChromeOptions()
    # options.add_argument('--headless=new') # ATIVAR DEPOIS NO GITHUB
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options, use_subprocess=True)

# --- MOTOR 1: INDEED ---
def buscar_vagas_indeed(termo_busca: str, local_busca: str = "") -> list:
    if local_busca:
        url = f"https://br.indeed.com/jobs?q={quote(termo_busca)}&l={quote(local_busca)}"
    else:
        url = f"https://br.indeed.com/jobs?q={quote(termo_busca)}"
    
    print(f"🔎 [Indeed] Buscando: '{termo_busca}' em '{local_busca}'...") 
    
    driver = None
    vagas = []

    try:
        driver = get_driver()
        driver.get(url)
        time.sleep(random.uniform(8, 12)) 

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        for card in job_cards:
            try:
                title_el = card.find('a', class_='jcs-JobTitle')
                company_el = card.find('span', {'data-testid': 'company-name'})
                local_el = card.find('div', {'data-testid': 'text-location'})
                salary_el = card.find('div', class_='salary-snippet-container')
                
                salario = "A combinar"
                if salary_el:
                    salario = salary_el.get_text(strip=True)
                else:
                    for item in card.find_all('div', {'class': 'metadata'}):
                        if 'R$' in item.get_text(): salario = item.get_text(strip=True); break
                    if salario == "A combinar":
                        for attr in card.find_all('div', {'data-testid': 'attribute_snippet_testid'}):
                            if 'R$' in attr.get_text(): salario = attr.get_text(strip=True); break
                
                if title_el:
                    link = f"https://br.indeed.com{title_el['href']}"
                    vagas.append({
                        'titulo': title_el.get_text(strip=True),
                        'empresa': company_el.get_text(strip=True) if company_el else "Confidencial",
                        'local': local_el.get_text(strip=True) if local_el else "Local n/a",
                        'salario': salario,
                        'link': link,
                        'fonte': 'indeed'
                    })
            except: pass
        return vagas
    except Exception as e:
        logging.error(f"Erro Indeed: {e}")
        return []
    finally:
        if driver: 
            try: driver.quit()
            except: pass

# --- MOTOR 2: QCONCURSOS ---
def buscar_qconcursos() -> list:
    # URL com filtros: PE (17) + Autorizado (2), Aberto (3), Inscrições Abertas (4)
    url = "https://www.qconcursos.com/concursos/pesquisa?by_situation%5B%5D=2&by_situation%5B%5D=3&by_situation%5B%5D=4&by_state%5B%5D=17"
    
    print(f"🏛️ [QConcursos] Acessando Editais PE...")

    driver = None
    concursos = []

    try:
        driver = get_driver()
        driver.get(url)
        time.sleep(10) # Aguarda site carregar

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Tenta pegar os cards principais
        cards = soup.find_all('div', class_='q-card-primary')
        
        logging.info(f"QConcursos: {len(cards)} editais encontrados.")

        for card in cards:
            try:
                # Título
                title_div = card.find('h3', class_='q-card-primary__title')
                if not title_div: continue
                link_el = title_div.find('a')
                titulo = link_el.get_text(strip=True)
                link = f"https://www.qconcursos.com{link_el['href']}"
                
                # Status
                status_el = card.find('span', class_='q-tag')
                status = status_el.get_text(strip=True) if status_el else "Info"

                # Info Extra
                info_div = card.find('div', class_='q-card-primary__info')
                info_texto = info_div.get_text(" | ", strip=True) if info_div else ""

                concursos.append({
                    'titulo': titulo,
                    'empresa': "Órgão Público",
                    'local': "Pernambuco",
                    'salario': "Ver Edital",
                    'resumo_q': f"Status: {status}\nℹ️ {info_texto}",
                    'link': link,
                    'fonte': 'qconcursos'
                })
            except: pass
            
        return concursos

    except Exception as e:
        logging.error(f"Erro QConcursos: {e}")
        return []
    finally:
        if driver: 
            try: driver.quit()
            except: pass