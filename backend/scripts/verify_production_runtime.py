"""Production-side Atlas verification — Gate 1 + Gate 3 of P0 Trust Workstream.

Run inside the PRODUCTION pod only.
No code changes. No secrets modified. No JWT_SECRET, auth, RBAC, or sessions touched.

Expected output on success:
    AUTH: [{'user': 'masci_prod_user', 'db': 'admin'}]
    CROSS-DB masci_safety_preview: BLOCKED OperationFailure codeName=Unauthorized
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv('/app/backend/.env')


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    info = await client.admin.command('connectionStatus')
    print('AUTH:', info['authInfo']['authenticatedUsers'])
    try:
        cols = await client['masci_safety_preview'].list_collection_names()
        print(f'CROSS-DB masci_safety_preview: {len(cols)} cols VIOLATION')
    except Exception as e:  # noqa: BLE001
        code_name = getattr(e, 'details', {}).get('codeName')
        print(f'CROSS-DB masci_safety_preview: BLOCKED {type(e).__name__} codeName={code_name}')
    client.close()


if __name__ == '__main__':
    asyncio.run(main())
