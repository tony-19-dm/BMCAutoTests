from locust import HttpUser, task, between

BMC_IP = "https://localhost:2443"
USERNAME = "root"
PASSWORD = "0penBmc"

class BMCSystemInfoUser(HttpUser):
    host = BMC_IP
    wait_time = between(1, 5)

    def on_start(self):
        self.client.auth = (USERNAME, PASSWORD)
        self.client.verify = False  # Отключение проверки SSL (для тестов)

    @task
    def get_info(self):
        self.client.get("/redfish/v1/Systems/system")

class BMCPowerStateUser(HttpUser):
    host = BMC_IP
    wait_time = between(1, 5)

    def on_start(self):
        self.client.auth = (USERNAME, PASSWORD)
        self.client.verify = False
    
    @task
    def get_power_state(self):
        self.client.get("/redfish/v1/Systems/system/").json().get("PowerState")
