from validations import Validations
import pandas as pd
import asyncio
import aiohttp

API_URL = 'https://api-beta.banano.cc:443'


async def json_get(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
                return jsonResp
    except BaseException as e:
        print(e)
        print("Something went wrong!!!")


async def load_addresses():
    filename = input("Enter the csv payment list here: \n")
    try:
        data = pd.read_csv(filename)
        print(data)
        addresses = list(data["addresses"])
        print(addresses)
        valid_addresses = set()
        print(3)

        for address in addresses:
            if Validations.get_banano_address(address) is not None:
                valid_addresses.add(Validations.get_banano_address(address))
        print(valid_addresses)
        f = open("paid.txt", "r")
        previous = set(f.read().splitlines())
        print(previous)
        print(type(previous))
        unpaid = valid_addresses.difference(previous)
        print("Unpaid")
        print(unpaid)
        input()
        return unpaid
    except Exception as e:
        print(e)

    valid_addresses = set()
    return valid_addresses


async def get_pay():
    pay = ""
    while not isinstance(pay, int):
        pay = input("Enter how much each account is going to be paid here: \n")
        if pay == "0":
            print("Enter something greater than 0!")
            pay = ""
        else:
            try:
                pay = int(pay)
                return pay
            except Exception as e:
                print(e)
                print("Please enter an integer!\n")
    return 0


async def get_wallet():
    has_wallet = input("Do you already have a wallet on the node? [y/n]")
    if has_wallet in ["yes", "Yes", "Y", "y"]:
        walletID = input("Please enter your walletID: \n")
        return walletID
    if has_wallet in ["no", "No", "N", "n"]:
        has_seed = input("Do you have a seed to use for payments? [y/n]")
        if has_seed in ["yes", "Yes", "Y", "y"]:
            seed = input("Please enter your seed: \n")
            payload = {
                "action": "wallet_create",
                "seed": seed
            }
            response = await json_get(payload)
            walletID = response['wallet']
            print("WalletID-" + walletID)
            return walletID
    else:
        print("Generating a temporary wallet...\n")
        payload = {"action": "wallet_create"}
        response = await json_get(payload)
        try:
            walletID = response['wallet']
            print("WalletID-" + walletID)
            return walletID
        except:
            print(response)
            return None

async def saverun(walletID, depositAddress):
    print("Account and wallet ID are being save to lastrun.txt to minimise potential losses")
    file = open("lastrun.txt", "w")
    file.write("WalletID: " + walletID)
    file.write("\nAddress: " + depositAddress)
    file.close()

async def account_create(walletID):
    payload = {
        "action": "account_create",
        "wallet": walletID,
        "index": "0"
        }
    response = await json_get(payload)
    try:
        depositAddress = response['account']
        await saverun(walletID, depositAddress)
        return depositAddress
    except Exception as e:
        print(e)
        return None


async def get_balance(address):
    payload = {
        "action": "account_balance",
        "account": address
    }
    response = await json_get(payload)
    balance = response['balance']
    return balance


async def enough_bans(paymentadd, paytotal):
    balanceraw = await get_balance(paymentadd)
    balanceint = int(balanceraw) / 10 ** 29
    if paytotal <= int(balanceint):
        return True
    else:
        return False


async def send_payment(walletID, paymentadd, address, pay):
    payload = {
        "action": "send",
        "wallet": walletID,
        "source": paymentadd,
        "destination": address,
        "amount": str(pay * 10 ** 29),
    }
    try:
        response = await json_get(payload)
        block = response['block']
        print("Return block: " + block)
    except Exception as e:
        print(payload)
        print(e)


async def destroy_wallet(walletID):
    destroy = input("Do you want to destroy the wallet used? [y/n]")
    if destroy in ["yes", "Yes", "Y", "y"]:
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


async def main():
    addresses = await load_addresses()
    if len(addresses) > 0:
        pay = await get_pay()
        walletID = await get_wallet()
        paymentadd = await account_create(walletID)
        while not await enough_bans(paymentadd, len(addresses)*pay):
            input("Please ensure " + str(paymentadd) + " has enough bans to pay " + str(len(addresses)*pay) + "\n")
        total = len(addresses)

        f = open("paid.txt", "a+")
        for index, address in enumerate(addresses, start=1):
            print("Sending " + str(pay) + "ban to " + address + " - " + str(index) + "/" + str(total))
            await send_payment(walletID, paymentadd, address, pay)
            f.write(address + "\n")
        f.close()

        await destroy_wallet(walletID)


asyncio.run(main())
