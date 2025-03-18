from locust import HttpUser, task, between

HOST = "https://wttr.in"

class JsonplaceholderUser(HttpUser):
    host = HOST
    wait_time = between(1, 5)

    @task
    def get_posts(self):
        self.client.get("/Novosibirsk?format=j1")