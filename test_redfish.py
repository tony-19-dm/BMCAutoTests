import pytest
import requests
import time
import logging

BMC_IP = "localhost:2443"
USERNAME = "root"
PASSWORD = "0penBmc"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("py_log.log", mode="w")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(file_handler)

@pytest.fixture(scope="session")
def redfish_session():
    """Фикстура для аутентифицированной сессии Redfish"""
    session = requests.Session()
    session.verify = False

    auth_url = f"https://{BMC_IP}/redfish/v1/SessionService/Sessions"
    try:
        response = session.post(
            auth_url,
            json={
                "UserName": USERNAME,
                "Password": PASSWORD
            }
        )

        response.raise_for_status()
        token = response.headers.get("X-Auth-Token")

        if not token:
            logger.error("The authentication token is missing")
            pytest.fail("Токен аутентификации отсутствует")
        session.headers.update({"X-Auth-Token": token})
        logger.info("Successful authentication")

    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication error: {e}")
        pytest.fail(f"Не удалось создать сессию: {e}")

    yield session

    session_id = response.json().get("Id")
    if session_id:
        try:
            session.delete(f"{auth_url}/{session_id}")
            logger.info("Session deleted")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Session deletion error: {e}")

def test_authentication(redfish_session):
    """Тест успешной аутентификации"""
    assert redfish_session is not None, "Сессия не создана"

def test_system_info(redfish_session):
    """Тест получения информации о системе"""
    url = f"https://{BMC_IP}/redfish/v1/Systems/system"
    logger.info(f"Sending a GET request to {url}")
    
    response = redfish_session.get(url)
    logger.info(f"A response has been received. Status: {response.status_code}")

    assert response.status_code == 200, f"Неверный статус-код: {response.status_code}. Ответ: {response.text}"
    
    data = response.json()
    logger.debug(f"Ответ сервера: {data}")
    
    assert "Status" in data, f"Поле 'Status' отсутствует. Ответ: {data}"
    assert "PowerState" in data, f"Поле 'PowerState' отсутствует. Ответ: {data}"

def wait_for_power_state(session, system_url, expected_state, max_retries=5, delay=2):
    """Wait for system power state change"""
    logger.info(f"[Power State] Waiting for state '{expected_state}' (max attempts: {max_retries})")
    
    for attempt in range(1, max_retries + 1):
        logger.debug(f"[Power State] Attempt {attempt}/{max_retries} → GET {system_url}")
        response = session.get(system_url)
        
        if response.status_code != 200:
            logger.warning(f"[Power State] Request failed. Status: {response.status_code}, Response: {response.text[:200]}")
            continue
            
        current_state = response.json().get("PowerState")
        logger.debug(f"[Power State] Current state: {current_state}")
        
        if current_state == expected_state:
            logger.info(f"[Power State] Target state '{expected_state}' achieved")
            return True
            
        logger.debug(f"[Power State] Retrying in {delay} seconds...")
        time.sleep(delay)
    
    logger.error(f"[Power State] Failed to reach state '{expected_state}' after {max_retries} attempts")
    return False

def test_power_on(redfish_session):
    """Server power-on test"""
    system_url = f"https://{BMC_IP}/redfish/v1/Systems/system"
    reset_url = f"{system_url}/Actions/ComputerSystem.Reset"

    logger.info(f"[Power On] Sending POST to {reset_url}")
    payload = {"ResetType": "On"}
    
    try:
        response = redfish_session.post(reset_url, json=payload)
        logger.debug(f"[Power On] Response status: {response.status_code}, headers: {response.headers}")
        
        assert response.status_code == 202, (
            f"Expected 202 Accepted, got {response.status_code}. "
            f"Response: {response.text[:500]}"
        )
        logger.info("[Power On] Power-on command accepted (202)")
        
        logger.info("[Power On] Verifying power state...")
        success = wait_for_power_state(redfish_session, system_url, "On")
        
        assert success, "Power state did not change to 'On' within expected time"
        logger.info("[Power On] Power state changed to 'On' successfully")
        
    except Exception as e:
        logger.error(f"[Power On] Test failed: {str(e)}")
        raise
