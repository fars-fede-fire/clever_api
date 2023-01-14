from aiohttp import ClientSession, ClientResponse


class Login:
    "Exchange email for API key."

    def __init__(self, websession: ClientSession, email: str) -> None:
        self.websession = websession
        self.email = email
        self.headers = {"authorization": "Basic bW9iaWxlYXBwOmFwaWtleQ=="}

    async def request_login_email(self) -> ClientResponse:
        """Request login email to extract secretCode"""

        return await self.websession.request(
            "get",
            f"https://mobileapp-backend.clever.dk/api/mobile/customer/verifyEmail?email={self.email}",
            headers=self.headers,
        )

    async def exchange_secretCode(self, url: str) -> ClientResponse:
        """Exchange confirmation URL to API key"""

        secret_code = url.split("secretCode=")[1]

        resp = await self.websession.request(
            "get",
            f"https://mobileapp-backend.clever.dk/api/mobile/customer/verifySignupToken?token={secret_code}&email={self.email}",
            headers=self.headers,
        )

        answer = await resp.json()
        first_name = answer["data"]["firstName"]
        last_name = answer["data"]["lastName"]

        next_request = await self.websession.request(
            "post",
            "https://mobileapp-backend.clever.dk/api//v2/customer/registerProfile",
            json={
                "email": self.email,
                "firstName": first_name,
                "lastName": last_name,
                "token": secret_code,
            },
            headers=self.headers,
        )

        next_request_resp = await next_request.json()
        user_secret = next_request_resp["data"]["userSecret"]

        retrieve_api_key = await self.websession.request(
            "get",
            f"https://mobileapp-backend.clever.dk/api/mobile/customer/loginWithSecretCode?secret={user_secret}&email={self.email}",
            headers=self.headers,
        )

        retrieve_api_key_resp = await retrieve_api_key.json()
        api_key = retrieve_api_key_resp["data"]

        return api_key
