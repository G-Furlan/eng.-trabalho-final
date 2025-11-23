from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- CONFIGURAÇÃO ---
RUN_ID = input("Digite o ID do evento (mesmo do setup): ") 

BASE_URL = "http://127.0.0.1:5000"
SENHA = "SenhaForte123"

print(">>> INICIANDO JUÍZ AUTOMÁTICO...")
driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 20)

def safe_click(element): 
    driver.execute_script("arguments[0].click();", element)

try:
    print(f">>> LOGANDO COMO BOSS_{RUN_ID}...")
    
    driver.get(f"{BASE_URL}/login")
    wait.until(EC.presence_of_element_located((By.NAME, "nickname_login")))
    driver.find_element(By.NAME, "nickname_login").send_keys(f"Boss_{RUN_ID}")
    driver.find_element(By.NAME, "senha_login").send_keys(SENHA)
    safe_click(driver.find_element(By.XPATH, "//form[@action='/login_submit']//button"))
    
    # Vai para Dashboard
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "logo")))
    driver.get(f"{BASE_URL}/dashboard")
    
    # Acha o evento e clica em Gerenciar
    nome_evento = f"Copa Selenium {RUN_ID}"
    print(f"   Procurando: {nome_evento}")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "card")))
    
    # XPath esperto para achar o botão do card certo
    xpath_btn = f"//h3[contains(text(), '{nome_evento}')]/parent::div//a[contains(@class, 'btn-card-edit')]"
    btn_gerenciar = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_btn)))
    safe_click(btn_gerenciar)
    
    # Entra em Gerenciar Inscrições
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detalhe-header")))
    safe_click(driver.find_element(By.XPATH, "//a[contains(text(), 'Gerenciar Inscrições')]"))
    
    # --- FASE 1: PONTOS ---
    print(">>> DISTRIBUINDO PONTOS...")
    wait.until(EC.presence_of_all_elements_located((By.NAME, "pontos")))
    
    # Dá pontos para os 4 primeiros (100, 90, 80, 70)
    pontos = [100, 90, 80, 70]
    
    for i, pts in enumerate(pontos):
        inputs = driver.find_elements(By.NAME, "pontos")
        botoes = driver.find_elements(By.CLASS_NAME, "btn-icon-save")
        
        if i >= len(inputs): break
        
        campo = inputs[i]
        botao = botoes[i]
        
        campo.clear()
        campo.send_keys(str(pts))
        safe_click(botao)
        print(f"   > Jogador {i+1}: {pts} pts")
        
        try: wait.until(EC.staleness_of(campo))
        except: pass
        wait.until(EC.presence_of_element_located((By.NAME, "pontos")))
        time.sleep(0.2)

    # --- FASE 2: GERAR CHAVES ---
    print(">>> GERANDO CHAVES...")
    driver.execute_script("window.scrollTo(0, 0);")
    safe_click(driver.find_element(By.XPATH, "//a[contains(text(), 'Gerar Chaves')]"))
    
    try: 
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except: pass
    
    wait.until(EC.url_contains("/chaves"))
    print("   > Mata-mata iniciado!")

    # --- FASE 3: SIMULAR O TORNEIO ATÉ O FIM ---
    print(">>> SIMULANDO PARTIDAS...")
    
    # Loop infinito até chegar na página de relatório
    rodada = 1
    while "relatorio" not in driver.current_url:
        try:
            # Procura qualquer botão "Venceu" disponível na tela
            # O wait é curto pq se não tiver botão, pode ser que acabou
            btns_vencer = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "btn-win"))
            )
            
            if btns_vencer:
                print(f"   > Definindo vencedor da partida {rodada}...")
                # Clica no PRIMEIRO botão que aparecer (o jogador de cima sempre ganha no nosso teste)
                safe_click(btns_vencer[0])
                rodada += 1
                time.sleep(1) # Espera a página recarregar
            else:
                print("   ? Nenhum botão de vencer encontrado. Verificando...")
                time.sleep(2)
                
        except Exception as e:
            # Se deu erro de timeout procurando botão, verifica se mudou de página
            if "relatorio" in driver.current_url:
                break
            print("   ! Aguardando próximo passo...")
            time.sleep(1)

    # --- FIM: RELATÓRIO ---
    print("\n" + "="*40)
    print("🏆 TEMOS UM CAMPEÃO!")
    print("✅ Redirecionado para o Relatório Final.")
    
    # Pega o nome do campeão na tela
    try:
        campeao_nome = driver.find_element(By.TAG_NAME, "h1").text
        print(f"🥇 O Grande Vencedor foi: {campeao_nome}")
    except:
        pass
        
    print("="*40)
    time.sleep(5) # Deixa você ver o resultado

except Exception as e:
    print(f"\n❌ Erro: {e}")
    driver.save_screenshot("erro_final.png")