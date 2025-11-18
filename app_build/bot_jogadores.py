from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import random

# --- CONFIGURAÇÕES ---
# COLOQUE AQUI O ID DO EVENTO QUE VOCÊ CRIOU NO SETUP
RUN_ID = input("Digite o ID do evento (ex: 452): ") 

BASE_URL = "http://127.0.0.1:5000"
SENHA = "SenhaForte123"
QTD_JOGADORES = 8 

print(">>> INICIANDO ROBÔ V2 (MODO PACIENTE)...")
driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 20) # 20 segundos de paciência máxima

def safe_click(element): 
    driver.execute_script("arguments[0].click();", element)

# --- NOVA FUNÇÃO MÁGICA: PREENCHER COM TENTATIVAS ---
def preencher_campo(by, identificador, texto, tentativas=3):
    """Tenta preencher um campo. Se der erro (Stale), tenta de novo."""
    for i in range(tentativas):
        try:
            # 1. Espera o campo existir
            wait.until(EC.presence_of_element_located((by, identificador)))
            # 2. Busca o elemento (sempre busca "fresco")
            campo = driver.find_element(by, identificador)
            # 3. Limpa e escreve
            campo.clear()
            campo.send_keys(texto)
            return # Sucesso! Sai da função
        except Exception as e:
            print(f"   [!] Engasgo no campo '{identificador}'. Tentando de novo ({i+1}/{tentativas})...")
            time.sleep(1) # Respira 1 segundo antes de tentar de novo
    raise Exception(f"❌ Não consegui preencher o campo {identificador} após {tentativas} tentativas.")

def selecionar_dropdown(name, valor):
    wait.until(EC.presence_of_element_located((By.NAME, name)))
    select = Select(driver.find_element(By.NAME, name))
    select.select_by_value(valor)

def logout():
    driver.get(f"{BASE_URL}/logout")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hero-section")))

try:
    print(f">>> INSCREVENDO JOGADORES NO EVENTO {RUN_ID}...")
    nome_evento_alvo = f"Copa Selenium {RUN_ID}"

    for i in range(1, QTD_JOGADORES + 1):
        time.sleep(1) # Pausa inicial
        
        p_name = f"Player_{i}_{RUN_ID}"
        print(f"--- Processando {p_name} ---")
        
        # 1. Cadastro (Usando a função blindada)
        driver.get(f"{BASE_URL}/login")
        
        try:
            selecionar_dropdown("tipo_usuario", "jogador")
            
            preencher_campo(By.NAME, "nickname", p_name)
            preencher_campo(By.NAME, "senha", SENHA)
            preencher_campo(By.NAME, "telefone", "99999999")
            preencher_campo(By.NAME, "idade", "22")
            preencher_campo(By.NAME, "email", f"p{i}_{RUN_ID}@t.com")
            
            # Clica em Cadastrar
            btn_cadastrar = driver.find_element(By.XPATH, "//form[@action='/register']//button")
            safe_click(btn_cadastrar)
            
            # Espera voltar pro login (confirmação)
            wait.until(EC.presence_of_element_located((By.NAME, "nickname_login")))
            
        except Exception as e:
            print(f"❌ Erro no cadastro: {e}")
            driver.save_screenshot(f"erro_cadastro_{p_name}.png")
            continue # Pula pro próximo

        # 2. Login
        try:
            preencher_campo(By.NAME, "nickname_login", p_name)
            preencher_campo(By.NAME, "senha_login", SENHA)
            
            btn_login = driver.find_element(By.XPATH, "//form[@action='/login_submit']//button")
            safe_click(btn_login)
            
            # Espera o menu
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "logo")))
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            continue

        # 3. Achar Evento
        driver.get(f"{BASE_URL}/eventos")
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "calendar-grid")))
            
            # Procura o botão "Ver Detalhes" específico desse evento
            xpath_evento = f"//h3[contains(text(), '{nome_evento_alvo}')]/following-sibling::a"
            
            # Tenta clicar com scroll
            btn_detalhes = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_evento)))
            driver.execute_script("arguments[0].scrollIntoView();", btn_detalhes)
            time.sleep(0.5)
            safe_click(btn_detalhes)
            
        except:
            print(f"❌ Não achei o evento '{nome_evento_alvo}'! (Verifique o ID)")
            logout()
            break
            
        # 4. Inscrever
        try:
            # Espera carregar a página de detalhes
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detalhe-header")))
            
            # Procura o botão "Quero Participar"
            # Se não achar em 3 segundos, assume que já está inscrito ou deu erro
            try:
                btn_part = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Quero Participar')]"))
                )
                safe_click(btn_part)
                
                # Espera virar cancelar
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "btn-cancelar")))
                print("   ✅ Inscrito com sucesso.")
            except:
                print("   ⚠️ Botão participar não apareceu (provavelmente já inscrito).")

        except Exception as e:
            print(f"❌ Erro na página de detalhes: {e}")

        logout()

    print("\n✅ PROCESSO FINALIZADO!")

except Exception as e:
    print(f"❌ Erro fatal: {e}")