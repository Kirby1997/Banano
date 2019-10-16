import asyncio
import aiohttp
import aiofiles
import json

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


async def get_history(address, noTrans = 1):
    payload = {"action": "account_history", "account": address, "count": noTrans}
    response = await json_get(payload)
    return response['history']


async def read_file():
    known_labels = {}
    async with aiofiles.open('exchanges.txt') as f:
        linenum = 0
        async for line in f:
            linenum += linenum
            keypair = line.strip()
            keypair = keypair.split(":")
            try:
                known_labels[keypair[0]] = keypair[1]
            except:
                print("inconsistency at line {} containing \"{}\" ".format(linenum, line))
                print("Formatting should be address:label")
    return known_labels


async def main():
    source = input("Enter an address to find exchange wallets for: ")
    noTrans = input("How many transactions should be retrieved: ")
    known_labels = await read_file()
    # Get the account's search history
    history = await get_history(source, int(noTrans))
    addresses = set()
    intermediaries = {}
    # Add the addresses in the history to a list
    for i in history:
        if i['type'] == "send":
            addresses.add(i['account'])
    # Get the history of the addresses in the list
    for i in addresses:
        history = await get_history(i, 6)
        for x in history:
            if x['account'] in known_labels and x['type'] == "send" and i not in intermediaries:
                intermediaries[i] = known_labels[x['account']]

    print(json.dumps(intermediaries, indent=4))


asyncio.run(main())
