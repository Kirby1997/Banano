import asyncio
import aiohttp
import csv
import os.path
import json
import aiofiles

API_URL = 'https://api-beta.banano.cc:443'


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


async def get_discord(account, users):
    for entry in users:
        if entry['address'] == account:
            totals[account][2] = entry["user_name"]


async def get_twitter(account, users):
    for entry in users:
        if entry[0] == account:
            totals[account][3] = entry[1]


async def get_telegram(account, users):
    for entry in users:
        if entry[0] == account:
            totals[account][4] = entry[1]


async def format_txt(file):
    file = file.strip("((")
    file = file.strip("))")
    names = []
    addresses = []
    for account in file.split("), ("):
        # print(account)
        account = account.split(", ")
        names.append(account[1].strip("\'") + " - " + account[0].strip("\'"))
        addresses.append(account[2].strip("\'"))

    zipped = zip(addresses, names)
    zipped = set(zipped)
    return zipped


async def get_inter(address, labels):
    if totals[address][2] != "":
        return ""
    else:
        history = await get_history(address, 1)
        for transaction in history:
            if transaction['account'] in labels and transaction['type'] == "send":
                totals[address][3] = labels[transaction['account']]


async def download_users():
    await download_discord()
    await download_telegram()
    await download_twitter()


async def download_discord():
    print("Downloading discord.json...")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://bananobotapi.banano.cc/users') as resp:
            with open("discord.json", "wb") as f:
                async for data in resp.content.iter_chunked(1024):
                    f.write(data)


async def download_twitter():
    print("Downloading twitter.txt...")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://ba.nanotipbot.com/users/twitter') as resp:
            with open("twitter.txt", "wb") as f:
                async for data in resp.content.iter_chunked(1024):
                    f.write(data)


async def download_telegram():
    print("Downloading telegram.txt...")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://ba.nanotipbot.com/users/telegram') as resp:
            with open("telegram.txt", "wb") as f:
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
    if not os.path.exists("discord.json") or not os.path.exists("telegram.txt") or not os.path.exists("twitter.txt"):
        skipdlusers = True
        await download_users()
    if not os.path.exists("exchanges.txt"):
        print("Downloading exchanges...")
        skipdlexch = True
        await download_exchanges()

    if not skipdlusers:
        update = input("Update user lists? \"yes\" or \"no\" (default no): ")
        if update in ["yes", "Yes", "Y", "y"]:
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
            # List is received, sent, Discord name, Twitter name, Telegram name, Exchange
            totals[destination] = [0, 0, "", "", "", ""]

        if transaction['type'] == "receive":
            totals[destination][0] = totals[destination][0] + int(amount)

        if transaction['type'] == "send":
            totals[destination][1] = totals[destination][1] + int(amount)

    print("Reading discord.json file...")
    with open("discord.json", "r") as f:
        users = json.load(f)

    print("Identifying Discord users...")
    coros = [get_discord(address, users) for address in totals]
    await asyncio.gather(*coros)

    print("Reading twitter.txt file...")
    with open("twitter.txt", "r") as f:
        twitter = f.read()
        twitter = await format_txt(twitter)

    print("Identifying Twitter users...")
    coros = [get_twitter(address, twitter) for address in totals]
    await asyncio.gather(*coros)

    print("Reading telegram.txt file...")
    with open("telegram.txt", "r", encoding="utf-8") as f:
        telegram = f.read()
        telegram = await format_txt(telegram)

    print("Identifying Telegram users...")
    coros = [get_telegram(address, telegram) for address in totals]
    await asyncio.gather(*coros)

    print("Loading in exchange list...")
    labels = await read_exchanges()

    print("Searching for intermediaries to exchanges and gambling sites...")
    coros = [get_inter(address, labels) for address in totals]
    await asyncio.gather(*coros)

    csv_columns = ['Address', 'Received', 'Sent', 'Discord', 'Twitter', 'Telegram', 'Exchange']
    csv_file = "totals.csv"
    try:
        print("Writing totals to totals.csv")
        with open(csv_file, 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_columns)
            for address in totals:
                writer.writerow([address, totals[address][0], totals[address][1], totals[address][2], totals[address][3], totals[address][4], totals[address][5]])
    except IOError as e:
        print(e)


asyncio.run(main())
