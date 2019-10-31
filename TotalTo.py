import asyncio
import aiohttp
import csv
import os.path
import json
import aiofiles

API_URL = 'https://api-beta.banano.cc:443'
UFW_API = 'https://bananobotapi.banano.cc/ufw/'


async def json_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
                return jsonResp
    except Exception as e:
        print(e)
        return None

async def get_history(address, noTrans = 50):
    payload = {"action": "account_history", "account": address, "count": noTrans}
    response = await json_get(payload)
    return response['history']


async def get_discord(account):
    with open("users.json", "r") as f:
        users = json.load(f)
        for entry in users:
            if entry['address'] == account:
                return entry["user_name"]
        return ""


async def get_inter(address, labels):
    if totals[address][2] != "":
        return ""
    else:
        history = await get_history(address, 1)
        for transaction in history:
            if transaction['account'] in labels and transaction['type'] == "send":
                totals[address][3] = labels[transaction['account']]


async def download_users():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://bananobotapi.banano.cc/users') as resp:
            with open("users.json", "wb") as f:
                async for data in resp.content.iter_chunked(1024):
                    f.write(data)


async def download_exchanges():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://raw.githubusercontent.com/Kirby1997/Banano/master/exchanges.txt') as resp:
            with open("exchanges.txt", "wb") as f:
                async for data in resp.content.iter_chunked(1024):
                    f.write(data)


async def read_exchanges():
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


async def check_updates():
    skipdlusers = False
    skipdlexch = False
    if not os.path.exists("users.json"):
        print("Downloading users.json...")
        skipdlusers = True
        await download_users()
    if not os.path.exists("exchanges.txt"):
        print("Downloading exchanges...")
        skipdlexch = True
        await download_exchanges()

    if not skipdlusers:
        update = input("Update Discord users file? \"yes\" or \"no\" (default no): ")
        if update in ["yes", "Yes", "Y", "y"]:
            print("Downloading users.json...")
            await download_users()
    if not skipdlexch:
        update = input("Update exchanges file? \"yes\" or \"no\" (default no): ")
        if update in ["yes", "Yes", "Y", "y"]:
            print("Downloading exchanges.txt...")
            await download_exchanges()


# Dictionary to use an address as a key and store attributes in a list.
totals = {}

async def main():
    source = input("Enter an address to see transaction totals for: ")
    noTrans = input("How many transactions should be retrieved (default 50): ")
    await check_updates()
    if noTrans == "":
        noTrans = 50

    print("Getting the last ", noTrans, " transactions...")
    history = await get_history(source, noTrans)


    print("Searching history of account...")
    for transaction in history:
        amount = int(transaction['amount']) / 10 ** 29
        destination = transaction['account']
        if destination not in totals:
            # List is received, sent, Discord name, Exchange
            totals[destination] = list([0, 0, "", ""])

        if transaction['type'] == "receive":
            totals[destination][0] = totals[destination][0] + int(amount)

        if transaction['type'] == "send":
            totals[destination][1] = totals[destination][1] + int(amount)

    print("Identifying Discord users...")
    coros = [get_discord(address) for address in totals]
    names = await asyncio.gather(*coros)

    for address, name in zip(totals, names):
        totals[address][2] = name

    print("Loading in exchange list...")
    labels = await read_exchanges()

    print("Searching for intermediaries to exchanges and gambling sites...")
    coros = [get_inter(address, labels) for address in totals]
    await asyncio.gather(*coros)

    csv_columns = ['Address', 'Received', 'Sent', 'Discord', 'Exchange']
    csv_file = "totals.csv"
    try:
        print("Writing totals to totals.csv")
        with open(csv_file, 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_columns)
            for address in totals:
                writer.writerow([address, totals[address][0], totals[address][1], totals[address][2], totals[address][3]])
    except IOError as e:
        print(e)


asyncio.run(main())

