from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import random

BASE_URL = "http://127.0.0.1:5000"
SENHA = "SenhaForte123"
# ID único para não dar conflito se rodar várias vezes
RUN_ID = random.randint(100, 999) 

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 10)

def safe_click(element): driver.execute_script("arguments[0].click();", element)
def set_js(eid, val): driver.execute_script(f"document.getElementById('{eid}').value = '{val}';")

try:
    print(f">>> SETUP INICIADO (ID: {RUN_ID})")
    
    # 1. Criar Organizador
    driver.get(f"{BASE_URL}/login")
    Select(driver.find_element(By.NAME, "tipo_usuario")).select_by_value("organizador")
    driver.find_element(By.NAME, "nickname").send_keys(f"Boss_{RUN_ID}")
    driver.find_element(By.NAME, "senha").send_keys(SENHA)
    driver.find_element(By.NAME, "email").send_keys(f"boss{RUN_ID}@test.com")
    safe_click(driver.find_element(By.XPATH, "//form[@action='/register']//button"))
    
    # 2. Login
    wait.until(EC.presence_of_element_located((By.NAME, "nickname_login")))
    driver.find_element(By.NAME, "nickname_login").send_keys(f"Boss_{RUN_ID}")
    driver.find_element(By.NAME, "senha_login").send_keys(SENHA)
    safe_click(driver.find_element(By.XPATH, "//form[@action='/login_submit']//button"))
    
    # 3. Criar Evento
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "logo")))
    driver.get(f"{BASE_URL}/evento/criar")
    
    driver.find_element(By.NAME, "nome").send_keys(f"Copa Selenium {RUN_ID}")
    driver.find_element(By.NAME, "jogo").send_keys("Selenium Fight")
    set_js("data", "2025-12-25")
    set_js("horario", "14:00")
    
    # IMPORTANTE: Define 4 vagas para o mata-mata
    Select(driver.find_element(By.NAME, "vagas_mata_mata")).select_by_value("4")
    
    driver.find_element(By.NAME, "local").send_keys("Arena Server")
    safe_click(driver.find_element(By.TAG_NAME, "button"))
    
    wait.until(EC.url_contains("/dashboard"))
    
    print("\n" + "="*40)
    print(f"✅ SETUP CONCLUÍDO!")
    print(f"Evento: Copa Selenium {RUN_ID}")
    print(f"Organizador: Boss_{RUN_ID}")
    print(f"Senha: {SENHA}")
    print("="*40)

except Exception as e:
    print(f"❌ Erro no Setup: {e}")
    driver.save_screenshot("erro_setup.png")