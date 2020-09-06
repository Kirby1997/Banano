import asyncio
import aiohttp
import csv
import os.path
import json
import aiofiles
import bananopy.banano as ban


async def get_history(address, noTrans = 50):
    pagesize = 3000

    if noTrans <= pagesize:
        history = ban.account_history(address, noTrans)
        return history["history"]

    else:

        rem = noTrans % pagesize
        pages = (noTrans - rem) / pagesize
        count = 0
        offset = 0
        full_history = []

        while count < pages:
            print("Downloading history: Page " + str(count+1) + "/" + str(pages))
            history = ban.account_history(address, pagesize, offset=offset)
            count = count + 1
            full_history = full_history + history["history"]
            offset = offset + pagesize

        if rem != 0:
            history = ban.account_history(address, rem, offset=offset)
            full_history = full_history + history["history"]
        return full_history


async def get_discord(account, users):
    for entry in users:
        if entry['address'] == account:
            totals[account][2] = entry["user_last_known_name"]


async def get_twitter(account, users):
    for entry in users:
        if entry['account'] == account:
            totals[account][3] = entry["user_name"]


async def get_telegram(account, users):
    for entry in users:
        if entry['account'] == account:
            totals[account][4] = entry["user_name"]


async def get_inter(address, labels):
    if totals[address][2] == "" or totals[address][3] == "" or totals[address][4] == "":
        history = await get_history(address, 1)
        await asyncio.sleep(0.5)
        for transaction in history:
            if transaction['account'] in labels and transaction['type'] == "send":
                print(labels[transaction['account']])
                totals[address][5] = labels[transaction['account']]


async def set_filename(account, discord, twitter, telegram):
    for entry in discord:
        if entry['address'] == account:
            filename = entry["user_last_known_name"] + " - " + account + ".csv"
            #filename = account + ".csv"
            return filename
    for entry in twitter:
        if entry['account'] == account:
            filename = entry['user_name'] + " - " + account + ".csv"
            return filename
    for entry in telegram:
        if entry['account'] == account:
            filename = entry['user_name'] + " - " + account + ".csv"
            return filename

    return account + ".csv"


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
    print("Downloading twitter.json...")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://ba.nanotipbot.com/users/twitter') as resp:
            with open("twitter.json", "wb") as f:
                async for data in resp.content.iter_chunked(1024):
                    f.write(data)


async def download_telegram():
    print("Downloading telegram.json...")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://ba.nanotipbot.com/users/telegram') as resp:
            with open("telegram.json", "wb") as f:
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
    if not os.path.exists("discord.json") or not os.path.exists("telegram.json") or not os.path.exists("twitter.json"):
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
    history = await get_history(source, int(noTrans))
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
        discord = json.load(f)

    print("Identifying Discord users...")
    coros = [get_discord(address, discord) for address in totals]
    await asyncio.gather(*coros)

    print("Reading twitter.json file...")
    with open("twitter.json", "r") as f:
        twitter = json.load(f)

    print("Identifying Twitter users...")
    coros = [get_twitter(address, twitter) for address in totals]
    await asyncio.gather(*coros)

    print("Reading telegram.json file...")
    with open("telegram.json", "r", encoding="utf-8") as f:
        telegram = json.load(f)

    print("Identifying Telegram users...")
    coros = [get_telegram(address, telegram) for address in totals]
    await asyncio.gather(*coros)

    print("Loading in exchange list...")
    labels = await read_exchanges()

    #print("Searching for intermediaries to exchanges and gambling sites...")
    #inters = [get_inter(address, labels) for address in totals]
    #await asyncio.gather(*inters)
    #print("Please wait 10 seconds...")
    #await asyncio.sleep(10)

    csv_columns = ['Address', 'Received', 'Sent', 'Discord', 'Twitter', 'Telegram', 'Exchange']

    filename = await set_filename(source, discord, twitter, telegram)

    try:
        print("Writing totals to " + filename)
        with open(filename, 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_columns)
            for address in totals:
                writer.writerow([address, totals[address][0], totals[address][1], totals[address][2], totals[address][3], totals[address][4], totals[address][5]])
    except IOError as e:
        print(e)


asyncio.run(main())
