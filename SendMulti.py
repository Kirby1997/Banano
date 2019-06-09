import aiohttp
import asyncio
import json
import aiofiles

API_URL = 'https://api-beta.banano.cc:443'


async def json_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json(content_type=None)
                return jsonResp
    except BaseException:
        print("Something went wrong. To prevent malfunction please withdraw your bans!!!")
        walletID = payload['wallet']
        source = payload['source']
        await return_spare(walletID, source)
        return None


async def create_wallet():
    payload = {"action": "wallet_create"}
    response = await json_get(payload)
    try:
        walletID = response['wallet']
        print("WalletID: " + walletID)
        return walletID
    except:
        return None


async def account_create(walletID):
    payload = {
        "action": "account_create",
        "wallet": walletID,
        "index": "1"
        }
    response = await json_get(payload)
    try:
        print("Account and wallet ID are being save to lastrun.txt to minimise potential losses")
        depositAddress = response['account']
        file = open("lastrun.txt", "w")
        file.write("WalletID: " + walletID)
        file.write("\nAddress: " + depositAddress)
        file.close()
        return depositAddress
    except:
        return None


async def send_funds(walletID, source):
    num_lines = sum(1 for line in open('addresses.txt'))
    sourcebal = await get_balance(source)
    sourcebal = int(sourcebal)/10**29
    remainder = sourcebal % num_lines
    banperacc = (sourcebal-remainder)/num_lines
    print("Sending " + str(banperacc) + "ban to each account!")
    async with aiofiles.open("addresses.txt") as file:
        async for account in file:
            account = account.strip()
            payload = {
                "action": "send",
                "wallet": walletID,
                "source": source,
                "destination": account,
                "amount": str(int(banperacc)*10**29),
                "id": source+account
            }
            print("Sending " + str(banperacc) + "ban to " + account)
            response = await json_get(payload)
            try:
                block = response['block']
            except:
                print(response)
                await return_spare(walletID, source)
            print("Account: " + account + ":block: " + block)


async def destroy_wallet(walletID):
    print("\nDestroying wallet...")
    payload = {
        "action": "wallet_destroy",
        "wallet": walletID
    }
    response = await json_get(payload)
    if response['destroyed'] == "1":
        print("Wallet has been destroyed")
    else:
        print("Wallet wasn't destroyed for some reason")


async def return_spare(walletID, depositAddress):
    balanceraw = await get_balance(depositAddress)
    balanceint = int(balanceraw)/10**29
    print("\nThe temporary deposit address still has " + str(balanceint) + "ban remaining!")
    returnAddr = input("Enter the banano address you would like to return the spare to \n")
    payload = {
        "action": "send",
        "wallet": walletID,
        "source": depositAddress,
        "destination": returnAddr,
        "amount": balanceraw,
        "id": walletID + returnAddr + "return"
    }
    response = await json_get(payload)
    block = response['block']
    print("Return block: " + block)


async def get_balance(address):
    payload = {
        "action": "account_balance",
        "account": address
    }
    response = await json_get(payload)
    balance = response['balance']
    return balance


async def main():
    print('This tool is for sending out bulk transactions of the same size from a list of addresses')
    print("USE AT YOUR OWN RISK")
    print("The node in use is the public Banano node found at nanoo.tools. If using regularly on a large scale, please direct at your own node")
    accept = input("I am not accountable for any losses from using this tool. Type \"Y\" if you agree \n")
    if accept == "y" or accept == "Y":
        print("\nCreating an account to deposit funds to...")
        walletID = await create_wallet()
        depositAddress = await account_create(walletID)
        print("Deposit funds you want split to this address: " + depositAddress)
        print("ENSURE ADDRESS IS COPIED CORRECTLY AS FUNDS CANNOT BE RETURNED")
        input("Press enter once funds have been RECEIVED (check creeper.banano.cc/explorer/account/" + depositAddress + ")\n")
        print("Sending funds to all accounts...")
        await send_funds(walletID, depositAddress)
        print("Funds sent...")
        await return_spare(walletID, depositAddress)
        await destroy_wallet(walletID)

    else:
        return None


asyncio.run(main())
