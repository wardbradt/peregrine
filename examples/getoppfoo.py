from peregrinearb import get_opportunity_for_market
import asyncio

opportunity = asyncio.get_event_loop().run_until_complete(get_opportunity_for_market("BTC/USD"))
print(opportunity)
