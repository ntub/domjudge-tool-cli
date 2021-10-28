from .base import V4Client


class GeneralAPI(V4Client):
    async def version(self):
        path = self.make_resource("/version")
        result = await self.get(path)
        return result.get("api_version")
