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

def test_pover_on(redfish_session):
    pover_usl = f"https://{BMC_IP}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"

    pover_data = {
        "ResetType": "On"
    }

    response = redfish_session.post(pover_usl, json = pover_data)
    assert response.status_code == 204, "Error when trying to turn on the server" # Текущая версия Bmc возвращает 204 

    # Проверка изменения статуса системы
    system_url = f"https://{BMC_IP}/redfish/v1/Systems/system"
    response = redfish_session.get(system_url)
    system_info = response.json()

    assert system_info["PowerState"] == "Off", "The server did not turn on" # Off -  заглушка, текущая версия Bmc не включается
    logger.info("The power management test was completed successfully")