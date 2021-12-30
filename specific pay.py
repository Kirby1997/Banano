from validations import Validations
import pandas as pd
import asyncio
import aiohttp
import decimal

API_URL = ''
PIPPIN = ""


async def toraw(amount):
    decimal.getcontext().prec = 41
    if len(str(amount)) > 42:
        return "Value too long"
    pay = decimal.Decimal(str(amount))
    neg = pay.as_tuple().exponent
    if neg < -29:
        return "Too many decimals"
    if len(str(int(pay))) > 12:
        return "Too many integers"
    exp = 29
    multiplier = 10 ** - neg
    raw = str(int(pay * multiplier) * 10 ** (exp + neg))
    return raw

async def json_get(payload, use_pippin=False):
    if use_pippin and PIPPIN != "":
        url = PIPPIN
    else:
        url = API_URL

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=100) as resp:
                jsonResp = await resp.json()
                return jsonResp
    except BaseException as e:
        print(e)
        print("Something went wrong!!!")


async def send_payment(walletID, paymentadd, address, pay):
    use_pippin = True
    payload = {
        "action": "send",
        "wallet": walletID,
        "source": paymentadd,
        "destination": address,
        "amount": await toraw(pay),
    }
    try:
        response = await json_get(payload, use_pippin)
        block = response['block']
        print("Return block: " + block)
        return block
    except Exception as e:
        print(payload)
        print(e)
        return "transaction failed"

async def get_wallet():
    use_pippin = True
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
            response = await json_get(payload, use_pippin)
            print(response)
            walletID = response['wallet']
            print("WalletID-" + walletID)
            return walletID
    else:
        print("Generating a temporary wallet...\n")
        payload = {"action": "wallet_create"}
        response = await json_get(payload, use_pippin)
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
    use_pippin = True
    if use_pippin and PIPPIN != "":
        payload = {
            "action": "account_list",
            "wallet": walletID
        }
        response = await json_get(payload, use_pippin)
        return response["accounts"][0]
    else:
        payload = {
            "action": "account_create",
            "wallet": walletID,
            "index": "0"
            }
        response = await json_get(payload, use_pippin)
        try:
            depositAddress = response['account']
            await saverun(walletID, depositAddress)
            return depositAddress
        except Exception as e:
            print(e)
            return None

async def enough_bans(paymentadd, paytotal):
    balanceraw = await get_balance(paymentadd)
    balanceint = int(balanceraw) / 10 ** 29
    if paytotal <= int(balanceint):
        return True
    else:
        return False

async def get_balance(address):
    payload = {
        "action": "account_balance",
        "account": address
    }
    response = await json_get(payload)
    balance = response['balance']
    return balance

async def destroy_wallet(walletID):
    use_pippin = True
    destroy = input("Do you want to destroy the wallet used? [y/n]")
    if destroy in ["yes", "Yes", "Y", "y", ""]:
        print("\nDestroying wallet...")
        payload = {
            "action": "wallet_destroy",
            "wallet": walletID
        }
        response = await json_get(payload, use_pippin)
        if response['destroyed'] == "1":
            print("Wallet has been destroyed")
        elif response['error'] == "Wallet not found":
            print("Wallet already deleted")
        else:
            print("Wallet wasn't destroyed for some reason! Use wallet destroy function to manually destroy it")


async def main():
    filename = input("Enter the csv payment list here: \n")
    data = pd.read_csv(filename)
    amounts = list(data["amount"])
    total = 0
    for amount in amounts:
        total = total + amount
    print("Total: " + str("%.2f" % total))
    print(data)

    walletID = await get_wallet()
    paymentadd = await account_create(walletID)

    while not await enough_bans(paymentadd, total):
        input("Please ensure " + str(paymentadd) + " has enough bans to pay " + str("%.2f" % total) + "banano\n")

    f = open("paid.txt", "a+")
    for index, row in data.iterrows():
        print(row[0]) # address
        if Validations.get_banano_address(row[0]) is not None:
            print("IT'S AN ADDRESS")
            print("Sending " + str(row[1]) + "ban to " + row[0] + " - " + str(index+1) + "/" + str(len(data)))
            block = await send_payment(walletID, paymentadd, row[0], row[1])
            f.write(row[0] + " - " + str(row[1]) + "\n Block: " + block + "\n")

        else:
            print("nonvalid")
    f.close()


    await destroy_wallet(walletID)


asyncio.run(main())