from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Inicializa o navegador
driver = webdriver.Chrome()

# Abre o site
driver.get("http://127.0.0.1:5000/jogadores")

# Espera a página carregar
time.sleep(1)

# Preenche o formulário de jogador
driver.find_element(By.NAME, "nome").send_keys("Teste Jogador")
driver.find_element(By.NAME, "email").send_keys("teste@teste.com")
driver.find_element(By.NAME, "idade").send_keys("20")
driver.find_element(By.NAME, "telefone").send_keys("123456789")
driver.find_element(By.NAME, "senha").send_keys("123@abc")
driver.find_element(By.TAG_NAME, "button").click()

time.sleep(1)

# Verifica se o jogador foi cadastrado (procura o nome na página)
assert "Teste Jogador" in driver.page_source
print("✅ Teste de cadastro de jogador passou!")

# Fecha o navegador
driver.quit()
