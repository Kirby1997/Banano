import asyncio
import aiohttp
import json

API_URL = 'https://api-beta.banano.cc:443'
UFW_API = 'https://bananobotapi.banano.cc/ufw/'


async def node_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
                return jsonResp
    except BaseException:
        print(BaseException)
        return None


async def get_rep(account):
    payload = {"action": "account_representative", "account": account}
    response = await node_get(payload)
    rep = response['representative']
    return rep


async def get_discord(account):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UFW_API+account) as resp:
                jsonResp = await resp.json()
                return jsonResp['user_name']
    except BaseException:
        print(BaseException)
        return None


async def main():
    source = input("Enter an address to find Discord connections for:  ")
    tranType = input("Do you want \"receive\" or \"send\" transaction totals? ")
    noTrans = input("How many transactions should be retrieved: ")
    if noTrans == "":
        noTrans = 1

    payload = {"action": "account_history", "account": source, "count": noTrans}

    response = await node_get(payload)
    addresses = set([])
    pairs = {}

    for i in response['history']:
        account = i['account']
        if account not in addresses:
            addresses.add(account)
            if i['type'] == tranType:
                rep = await get_rep(account)
                if rep == 'ban_1tipbotgges3ss8pso6xf76gsyqnb69uwcxcyhouym67z7ofefy1jz7kepoy':
                    user = await get_discord(account)
                    rep = user
                if rep == 'ban_1banbet1hxxe9aeu11oqss9sxwe814jo9ym8c98653j1chq4k4yaxjsacnhc':
                    rep = "BanBet"
                if rep == 'ban_1ka1ium4pfue3uxtntqsrib8mumxgazsjf58gidh1xeo5te3whsq8z476goo':
                    rep = "Kalium"
                pairs[account] = rep

    print(json.dumps(pairs, indent=4))

asyncio.run(main())
