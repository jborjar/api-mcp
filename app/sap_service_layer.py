import httpx
from config import get_settings


class SAPServiceLayerClient:
    def __init__(self):
        self._session_id: str | None = None
        self._settings = get_settings()

    async def login(self) -> str:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self._settings.SAP_B1_SERVICE_LAYER_URL}/Login",
                json={
                    "CompanyDB": self._settings.SAP_B1_COMPANY_DB,
                    "UserName": self._settings.SAP_B1_USER,
                    "Password": self._settings.SAP_B1_PASSWORD
                }
            )
            response.raise_for_status()
            self._session_id = response.cookies.get("B1SESSION")
            return self._session_id

    async def logout(self) -> None:
        if self._session_id:
            async with httpx.AsyncClient(verify=False) as client:
                await client.post(
                    f"{self._settings.SAP_B1_SERVICE_LAYER_URL}/Logout",
                    cookies={"B1SESSION": self._session_id}
                )
            self._session_id = None

    def _build_url(self, endpoint: str, include_count: bool = True) -> str:
        """Construye la URL con $inlinecount=allpages por defecto."""
        url = f"{self._settings.SAP_B1_SERVICE_LAYER_URL}/{endpoint}"
        if include_count:
            separator = "&" if "?" in endpoint else "?"
            url = f"{url}{separator}$inlinecount=allpages"
        return url

    def _get_headers(self, max_pagesize: int = 0) -> dict:
        """Retorna headers con Prefer odata.maxpagesize por defecto."""
        return {"Prefer": f"odata.maxpagesize={max_pagesize}"}

    async def get(self, endpoint: str, include_count: bool = True, max_pagesize: int = 0) -> dict:
        if not self._session_id:
            await self.login()
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                self._build_url(endpoint, include_count),
                cookies={"B1SESSION": self._session_id},
                headers=self._get_headers(max_pagesize)
            )
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: dict, include_count: bool = True, max_pagesize: int = 0) -> dict:
        if not self._session_id:
            await self.login()
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                self._build_url(endpoint, include_count),
                cookies={"B1SESSION": self._session_id},
                headers=self._get_headers(max_pagesize),
                json=data
            )
            response.raise_for_status()
            return response.json()
