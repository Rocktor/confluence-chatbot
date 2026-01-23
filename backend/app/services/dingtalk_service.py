import httpx
from app.config import settings
import structlog

logger = structlog.get_logger()

class DingTalkService:
    def __init__(self):
        self.app_key = settings.DINGTALK_APP_KEY
        self.app_secret = settings.DINGTALK_APP_SECRET
        self.base_url = "https://oapi.dingtalk.com"
        self.new_api_base = "https://api.dingtalk.com"

    async def get_access_token(self) -> str:
        """Get DingTalk enterprise access token"""
        url = f"{self.base_url}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("access_token")
            raise Exception(f"Failed to get access token: {data}")

    async def get_user_info_by_code(self, auth_code: str) -> dict:
        """Get user info by auth code using new API (3-step process)"""
        logger.info("Starting to get user info by auth code", auth_code=auth_code[:10] + "...")

        # Step 1: Get user personal token
        token_url = f"{self.new_api_base}/v1.0/oauth2/userAccessToken"
        token_data = {
            "clientId": self.app_key,
            "clientSecret": self.app_secret,
            "code": auth_code,
            "grantType": "authorization_code"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                token_url,
                json=token_data,
                headers={"Content-Type": "application/json"}
            )
            token_result = token_response.json()
            logger.info("User token response", data=token_result)

            access_token = token_result.get("accessToken")
            if not access_token:
                raise Exception(f"Failed to get user access token: {token_result}")

            # Step 2: Get user personal info
            user_info_url = f"{self.new_api_base}/v1.0/contact/users/me"
            user_info_response = await client.get(
                user_info_url,
                headers={
                    "x-acs-dingtalk-access-token": access_token,
                    "Content-Type": "application/json"
                }
            )
            user_info = user_info_response.json()
            logger.info("User personal info response", data=user_info)

            union_id = user_info.get("unionId")
            if not union_id:
                raise Exception("Failed to get unionId from user info")

            # Step 3: Get enterprise userid by unionId
            corp_access_token = await self.get_access_token()
            userid_url = f"{self.base_url}/topapi/user/getbyunionid"
            userid_response = await client.post(
                userid_url,
                json={"unionid": union_id},
                params={"access_token": corp_access_token},
                headers={"Content-Type": "application/json"}
            )
            userid_result = userid_response.json()
            logger.info("Enterprise userid response", data=userid_result)

            userid = None
            email = user_info.get("email")  # Try personal info first
            if userid_result.get("errcode") == 0:
                userid = userid_result.get("result", {}).get("userid")
                logger.info("Successfully got enterprise userid", userid=userid)

                # Get email from enterprise directory if not in personal info
                if not email and userid:
                    try:
                        user_detail = await self.get_user_detail(userid)
                        email = user_detail.get("email")
                        logger.info("Got email from enterprise directory", email=email)
                    except Exception as e:
                        logger.warn("Failed to get user detail", error=str(e))
            else:
                logger.warn("User not in enterprise directory", union_id=union_id, errcode=userid_result.get("errcode"))

            return {
                "userid": userid,
                "unionid": union_id,
                "openid": user_info.get("openId"),
                "name": user_info.get("nick"),
                "mobile": user_info.get("mobile"),
                "email": email
            }

    async def get_user_detail(self, user_id: str) -> dict:
        """Get detailed user information"""
        access_token = await self.get_access_token()
        url = f"{self.base_url}/topapi/v2/user/get"
        params = {"access_token": access_token}
        data = {"userid": user_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, json=data)
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("result")
            raise Exception(f"Failed to get user detail: {result}")
