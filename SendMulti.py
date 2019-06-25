import aiohttp
import asyncio
import json
import aiofiles
from validations import Validations

API_URL = 'https://api-beta.banano.cc:443'


async def json_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
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
        print(response)
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

async def load_seed():
    try:
        seed = input("Enter the seed of the account you want to use to distribute from: \n")
        payload = {
            "action": "wallet_create",
            "seed": seed
        }
        response = await json_get(payload)
        walletID = response['wallet']
        depositAddress = response['account']
        try:
            print("Account and wallet ID are being save to lastrun.txt to minimise potential losses")
            file = open("lastrun.txt", "w")
            file.write("WalletID: " + walletID)
            file.write("\nAddress: " + depositAddress)
            file.close()
            return walletID, depositAddress
        except:
            print("lastrun.txt could not be written")
            return walletID, depositAddress
    except:
        print("Something went wrong loading the seed")
        return None


async def send_funds(walletID, source):
    valid_addresses = set()
    async with aiofiles.open("addresses.txt") as file:
        async for line in file:
            if Validations.get_banano_address(line) is not None:
                account = Validations.get_banano_address(line)
                if Validations.validate_address(account) is True:
                    valid_addresses.add(account)
                else:
                    print(account + " is not a valid account")
            else:
                print(account + " does not fit the form of an address")
    num_addresses = len(valid_addresses)
    sourcebal = await get_balance(source)
    sourcebal = int(sourcebal)/10**29
    remainder = sourcebal % num_addresses
    banperacc = (sourcebal-remainder)/num_addresses
    print("Sending " + str(banperacc) + "ban to " + str(num_addresses) + " accounts!")
    for account in valid_addresses:
        account = account.strip()
        payload = {
            "action": "send",
            "wallet": walletID,
            "source": source,
            "destination": account,
            "amount": str(int(banperacc)*10**29),
            }
        print("Sending " + str(banperacc) + "ban to " + account)
        response = await json_get(payload)
        try:
            block = response['block']
            print("Account: " + account + ":block: " + block)
        except:
            print(response)
            await return_spare(walletID, source)


async def destroy_wallet(walletID):
    print("\nDestroying wallet...")
    payload = {
        "action": "wallet_destroy",
        "wallet": walletID
    }
    response = await json_get(payload)
    if response['destroyed'] == "1":
        print("Wallet has been destroyed")
    elif response['error'] == "Wallet not found":
        print("Wallet already deleted")
    else:
        print("Wallet wasn't destroyed for some reason! Use wallet destroy function to manually destroy it")


async def return_spare(walletID, depositAddress):
    balanceraw = await get_balance(depositAddress)
    balanceint = int(balanceraw)/10**29
    if balanceint == 0:
        return None
    else:
        print("\nThe temporary deposit address still has " + str(balanceint) + "ban remaining!")
        while True:
            returnAddr = input("Enter the banano address you would like to return the spare to \n")
            if Validations.get_banano_address(returnAddr) is not None:
                returnAddr = Validations.get_banano_address(returnAddr)
                if Validations.validate_address(returnAddr) is True:
                    print("Sending remaining bans to: " + returnAddr)
                    break
                else:
                    print(returnAddr + " is not a valid account")
            else:
                print(returnAddr + " does not fit the form of an address")
        payload = {
            "action": "send",
            "wallet": walletID,
            "source": depositAddress,
            "destination": returnAddr,
            "amount": balanceraw
        }
        try:
            response = await json_get(payload)
            block = response['block']
            print("Return block: " + block)
        except:
            print("Publishing block failed. Funds remain in distribution address\n " + payload)


async def get_balance(address):
    payload = {
        "action": "account_balance",
        "account": address
    }
    response = await json_get(payload)
    balance = response['balance']
    return balance


async def process_funds(walletID, depositAddress):
    print("Deposit funds you want split to this address: " + depositAddress)
    print("ENSURE ADDRESS IS COPIED CORRECTLY AS FUNDS CANNOT BE RETURNED")
    input(
        "Press enter once funds have been RECEIVED (check creeper.banano.cc/explorer/account/" + depositAddress + ")\n")
    print("Sending funds to all accounts...")
    await send_funds(walletID, depositAddress)
    print("Funds sent...")
    await return_spare(walletID, depositAddress)
    await destroy_wallet(walletID)


async def main():
    print('This tool is for sending out bulk transactions of the same size from a list of addresses')
    print("USE AT YOUR OWN RISK")
    print("The node in use is the public Banano node found at nanoo.tools. If using regularly on a large scale, please direct at your own node")
    accept = input("I am not accountable for any losses from using this tool. Type \"Y\" if you agree \n")
    if accept == "y" or accept == "Y":

        menu = {}
        menu['1'] = "Use random address"
        menu['2'] = "Use specific address (requires seed!!)"
        menu['3'] = "Destroy wallet on node (requires walledID)"
        menu['4'] = "Exit"
        while True:
            options = menu.keys()
            for entry in sorted(options):
                print(entry, menu[entry])
            selection = input("Please Select:")
            if selection == '1':
                print("\nCreating an account to deposit funds to...")
                walletID = await create_wallet()
                depositAddress = await account_create(walletID)
                await process_funds(walletID, depositAddress)
            elif selection == '2':
                print("This will distribute all of the bans in the account so ensure it only has the desired bans!!!")
                walletID, depositAddress = await load_seed()
                await process_funds(walletID, depositAddress)
            elif selection == '3':
                walletID = input("Enter the wallet ID you would like to destroy to help keep funds safu\n")
                await destroy_wallet(walletID)
                break
            elif selection == '4':
                print("Quitting")
                break
            else:
                print("Unknown Option Selected!")

    else:
        return None


asyncio.run(main())
