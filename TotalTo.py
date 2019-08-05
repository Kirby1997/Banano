import asyncio
import aiohttp


API_URL = 'https://api-beta.banano.cc:443'


async def json_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
                return jsonResp
    except BaseException:
        print(BaseException)
        return None


async def main():
    source = input("Enter an address to see transaction totals for ")
    tranType = input("Do you want \"receive\" or \"send\" transaction totals? ")
    noTrans = input("How many transactions should be retrieved: ")
    if noTrans == "":
        noTrans = 1

    payload = {"action": "account_history", "account": source, "count": noTrans}

    response = await json_get(payload)
    totals = {}
    for i in response['history']:
        amount = int(i['amount']) / 10 ** 29
        destination = i['account']

        if destination not in totals and i['type'] == tranType:
            totals[destination] = 0

        if i['type'] == tranType and i['account'] in totals:
            totals[destination] = totals[destination] + int(amount)

    print(totals)


asyncio.run(main())

input()

