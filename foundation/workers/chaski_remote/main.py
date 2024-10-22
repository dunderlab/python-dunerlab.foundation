import asyncio
import os
from chaski.remote import ChaskiRemote

# ----------------------------------------------------------------------
async def run(ip, port, name):
    """"""
    server = ChaskiRemote(
        ip=ip,
        port=port,
        name=name,
        available=os.getenv('modules', '').split(','),
        run=False,
    )

    print(f"CA Address: {server.address}")
    await server.run()


# ----------------------------------------------------------------------
def main(ip, port, name):
    """"""
    asyncio.run(run(ip, port, name))


main(ip='0.0.0.0', port=51112, name='Foundation Chaski Remote')
