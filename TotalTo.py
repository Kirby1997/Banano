import asyncio
import aiohttp
import json

API_URL = 'https://api-beta.banano.cc:443'
UFW_API = 'https://bananobotapi.banano.cc/ufw/'


async def json_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
                return jsonResp
    except BaseException:
        print(BaseException)
        return None


async def get_discord(account):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UFW_API+account) as resp:
                jsonResp = await resp.json()
                return jsonResp['user_name']
    except BaseException:
        print(BaseException)
        return account


async def main():
    source = input("Enter an address to see transaction totals for: ")
    tranType = input("Do you want \"receive\" or \"send\" transaction totals? ")
    noTrans = input("How many transactions should be retrieved: ")
    resolveDiscord = input("Attempt to resolve Discord usernames (slower)? \"yes\" or \"no\": ")
    if resolveDiscord in ["yes", "Yes", "Y", "y"]:
        resolveDiscord = True
    else:
        resolveDiscord = False
    if noTrans == "":
        noTrans = 1

    payload = {"action": "account_history", "account": source, "count": noTrans}

    response = await json_get(payload)
    totals = {}
    for i in response['history']:
        amount = int(i['amount']) / 10 ** 29
        destination = i['account']

        if destination not in totals and i['type'] == tranType:
            totals[destination] = [0]

        if (i['type'] == tranType or tranType == "") and i['account'] in totals:
            totals[destination] = [totals[destination][0] + int(amount)]

    if resolveDiscord:
        for destination in totals:
            discordName = await get_discord(destination)
            totals[destination].append(discordName)
    print(totals)
    totals = sorted(totals.items(), key=lambda kv: (kv[1], kv[0]))
    print(json.dumps(totals, indent=2))


asyncio.run(main())

