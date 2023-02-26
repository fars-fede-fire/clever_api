"""Testing API Wrapper"""
import asyncio
from yarl import URL

from clever_api.clever.clever import Util, Auth, Subscription, Evse


async def main():
    """Test API wrapper"""
    async with Evse(
        api_token="NTE2NDQyNSptb2JpbGVhcHAqNjk5MDg0MzM1NDgzNTAxOSo1NGE4NjZhOGEzMjJkYjVlMjgwNmJlNWU1NzM2ODQ1ZGZjODhkNjY3MDJiYmE1YWFhZmMyYWI2ZGJjZWZjYmM5",
        box_id=1456125,
        connector_id=1,
    ) as evse:
        data = await evse.set_flex(enable=True, effect=3, dept_time="06:00", kwh=20)
        print(data)


# async def main():
#    """Test API wrapper"""
#    async with Util() as util:
#        data = await util.get_energitillaeg()
#        print(data)
#        print(str(data.last_day_included))
#

if __name__ == "__main__":
    asyncio.run(main())
