from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# MESMO ID DO SETUP!
RUN_ID = input("Digite o ID do evento (mesmo do setup): ") 

BASE_URL = "http://127.0.0.1:5000"
SENHA = "SenhaForte123"

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 15)

def safe_click(element): driver.execute_script("arguments[0].click();", element)

try:
    print(f">>> LOGANDO COMO BOSS_{RUN_ID} PARA CLASSIFICAR...")
    
    # 1. Login Organizador
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.NAME, "nickname_login").send_keys(f"Boss_{RUN_ID}")
    driver.find_element(By.NAME, "senha_login").send_keys(SENHA)
    safe_click(driver.find_element(By.XPATH, "//form[@action='/login_submit']//button"))
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "logo")))
    driver.get(f"{BASE_URL}/dashboard")
    
    # 2. Achar Evento e Gerenciar
    nome_evento = f"Copa Selenium {RUN_ID}"
    print(f"Procurando evento: {nome_evento}")
    
    # Clica no botão Gerenciar do card certo
    xpath_btn = f"//h3[contains(text(), '{nome_evento}')]/parent::div//a[contains(@class, 'btn-card-edit')]"
    safe_click(driver.find_element(By.XPATH, xpath_btn))
    
    # Agora estamos em "Detalhes". Clicar em "Gerenciar Inscrições"
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detalhe-header")))
    safe_click(driver.find_element(By.XPATH, "//a[contains(text(), 'Gerenciar Inscrições')]"))
    
    # 3. Distribuir Pontos (Para os 4 primeiros da lista)
    print("Distribuindo pontos...")
    wait.until(EC.presence_of_element_located((By.NAME, "pontos")))
    
    pontos = [100, 90, 80, 70] # Pontuação para o Top 4
    
    for i, pts in enumerate(pontos):
        # Recarrega elementos a cada loop para evitar STALE ELEMENT
        inputs = driver.find_elements(By.NAME, "pontos")
        botoes_salvar = driver.find_elements(By.CLASS_NAME, "btn-icon-save")
        
        if i >= len(inputs): break # Se tiver menos de 4 jogadores
        
        campo = inputs[i]
        botao = botoes_salvar[i]
        
        campo.clear()
        campo.send_keys(str(pts))
        safe_click(botao)
        
        print(f"   > Jogador {i+1}: {pts} pontos.")
        # Espera recarregar (o campo fica stale)
        try: wait.until(EC.staleness_of(campo))
        except: pass
        wait.until(EC.presence_of_element_located((By.NAME, "pontos")))

    # 4. Gerar Chaves
    print("Gerando chaves...")
    safe_click(driver.find_element(By.XPATH, "//a[contains(text(), 'Gerar Chaves')]"))
    
    try: driver.switch_to.alert.accept()
    except: pass
    
    wait.until(EC.url_contains("/chaves"))
    print("\n✅ CHAVES GERADAS COM SUCESSO!")
    print("O mata-mata começou. Verifique no navegador.")
    time.sleep(10) # Deixa aberto pra você ver

except Exception as e:
    print(f"❌ Erro: {e}")
    driver.save_screenshot("erro_classificacao.png")