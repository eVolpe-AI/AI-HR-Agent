from tools.MintHCM.SuiteAPI import SuiteCRM, Module
from dotenv import load_dotenv
import os
load_dotenv()
class MintBaseTool():

    api_url = os.getenv("MINT_API_URL")
    client_id = os.getenv("MINT_CLIENT_ID")
    client_secret = os.getenv("MINT_CLIENT_SECRET")

    def get_connection(self) -> SuiteCRM:
        return SuiteCRM(
            client_id=self.client_id, 
            client_secret=self.client_secret, 
            url=self.api_url)