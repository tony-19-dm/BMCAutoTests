import pytest
import requests
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
    session.auth = (USERNAME, PASSWORD)
    session.verify = False
    yield session
    session.close()

def test_authentication(redfish_session):
    auth_url = f"https://{BMC_IP}/redfish/v1/SessionService/Sessions"

    response = redfish_session.post(
        auth_url,
        json={
            "UserName": USERNAME,
            "Password": PASSWORD
        }
    )

    assert response.status_code == 201, "Authentication error" # При выполнении post запрса возвращает 201
    session_info = response.json()
    assert "@odata.id" in session_info, "The Session token field is missing in the response"
    logger.info("The authentication test was completed successfuly")

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

def wait_for_power_state(session, system_url, expected_state):
    """Wait for system power state change"""
    logger.info(f"[Power State] Waiting for state '{expected_state}'")
    response = session.get(system_url)
    
    if response.status_code != 200:
        logger.warning(f"[Power State] Request failed. Status: {response.status_code}, Response: {response.text[:200]}")
        return False
        
    current_state = response.json().get("PowerState")
    logger.debug(f"[Power State] Current state: {current_state}")
    
    if current_state == expected_state:
        logger.info(f"[Power State] Target state '{expected_state}' achieved")
        return True
    
    logger.error(f"[Power State] Failed to reach state '{expected_state}'")
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
        
        assert response.status_code == 204, (
            f"Expected 202 Accepted, got {response.status_code}. "
            f"Response: {response.text[:500]}"
        )
        logger.info("[Power On] Power-on command accepted (202)")
        
        logger.info("[Power On] Verifying power state...")
        success = wait_for_power_state(redfish_session, system_url, "On")
        
        assert success, "Power state did not change to 'On'"
        logger.info("[Power On] Power state changed to 'On' successfully")
        
    except Exception as e:
        logger.error(f"[Power On] Test failed: {str(e)}")
        raise
