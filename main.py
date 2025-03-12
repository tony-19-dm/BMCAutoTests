import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time

@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
    yield driver
    driver.quit()

@pytest.fixture(autouse=True)
def logout_after_test(driver):
    yield
    try:
        wait = WebDriverWait(driver, 5)
        wait.until(EC.element_to_be_clickable(
            (By.ID, "app-header-user__BV_toggle_")
        )).click()
        
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@class, 'dropdown-item') and contains(., 'Log out')]")
        )).click()
    except Exception as e:
        print(f"Logout attempt failed: {str(e)}")

def test_success_login(driver):
    driver.get('https://localhost:2443/?next=/login#/login')
    wait = WebDriverWait(driver, 10)
    
    username = "root"
    password = "0penBmc"
    
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    header = wait.until(
        EC.visibility_of_element_located((By.ID, "page-header"))
    )
    assert header.is_displayed()

def test_failed_login(driver):
    driver.get('https://localhost:2443/?next=/login#/login')
    time.sleep(5)
    
    username = "root"
    password = "wrongpass"
    
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(5)

    errorWindow = driver.find_element(By.CLASS_NAME, 'neterror')
    
    assert errorWindow.is_displayed()

def test_ban_user(driver):
    driver.get('https://localhost:2443/?next=/login#/login')
    wait = WebDriverWait(driver, 10)
    
    # Правильные и неправильные пароли
    banning_username = "tony"
    banning_correct_password = "0penBmcc"       # Верный пароль
    banning_incorrect_password = "wrongpass"   # Неверный пароль

    # Первая попытка с правильным паролем и выход
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(banning_username)
    driver.find_element(By.ID, "password").send_keys(banning_correct_password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    wait.until(EC.element_to_be_clickable((By.ID, "app-header-user__BV_toggle_"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Log out')]"))).click()
    time.sleep(5)

    # Неудачные попытки (3 раза)
    for _ in range(3):
        username = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password = driver.find_element(By.ID, "password")
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")

        username.send_keys(banning_username)
        password.send_keys(banning_incorrect_password)
        login_btn.click()
        time.sleep(5)

    # Попытка входа с правильным паролем после блокировки
    username = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password = driver.find_element(By.ID, "password")
    login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    
    username.send_keys(banning_username)
    password.send_keys(banning_correct_password)
    login_btn.click()

    time.sleep(3)

    errorWindow = driver.find_element(By.CLASS_NAME, 'neterror')
    
    assert errorWindow.is_displayed()