import csv
import requests
import datetime
import time

# This script will calculate the value of each of your transactions and categorise transactions based on the services.
# This script relies on an export you can get from your account page at https://creeper.banano.cc


currencies = ["aed",
      "ars",
      "aud",
      "bch",
      "bdt",
      "bhd",
      "bmd",
      "bnb",
      "brl",
      "btc",
      "cad",
      "chf",
      "clp",
      "cny",
      "czk",
      "dkk",
      "eos",
      "eth",
      "eur",
      "gbp",
      "hkd",
      "huf",
      "idr",
      "ils",
      "inr",
      "jpy",
      "krw",
      "kwd",
      "lkr",
      "ltc",
      "mmk",
      "mxn",
      "myr",
      "ngn",
      "nok",
      "nzd",
      "php",
      "pkr",
      "pln",
      "rub",
      "sar",
      "sek",
      "sgd",
      "thb",
      "try",
      "twd",
      "uah",
      "usd",
      "vef",
      "vnd",
      "xag",
      "xau",
      "xdr",
      "xlm",
      "xrp",
      "zar",
      "bits",
      "link",
      "sats"] # CoinGecko supported currencies
print(currencies)
request_counter = 0
currency = input("Enter a currency from the list above...\n")
creeperfile = input("Enter Creeper Export file name...\n")



def get_intermediaries(addresses):
    batch_size = 35 # So that the URL isn't too long
    intermediaries = []
    base_url = "https://kirby.eu.pythonanywhere.com/api/v1/resources/intermediaries?"
    # Check all the addresses in the history against Kirby's intermediary API
    for i in range(0, len(addresses), batch_size):
        batch_addresses = addresses[i:i+batch_size]
        url = base_url + "&".join([f"address={addr}" for addr in batch_addresses])
        response = requests.get(url)
        intermediaries.extend(response.json())
    return intermediaries

def get_services(addresses, intermediaries):
    batch_size = 25 # So that the URL isn't too long
    services = []
    base_url = "https://kirby.eu.pythonanywhere.com/api/v1/resources/addresses?"
    for i in range(0, len(addresses), batch_size):
        batch_addresses = addresses[i:i+batch_size]
        url = base_url + "&".join([f"address={addr}" for addr in batch_addresses])
        response = requests.get(url)
        services.extend(response.json())

    # Get details about the intermediarys' services
    for i in range(0, len(intermediaries), batch_size):
        batch_addresses = [address["service"] for address in intermediaries[i:i+batch_size]]
        url = base_url + "&".join([f"address={addr}" for addr in batch_addresses])
        response = requests.get(url)
        response = response.json()
        for address in intermediaries:
            for service in response:
                if address["service"] == service["address"] and address["address"] not in services:
                    print(f"{address} --- {service}")
                    services.append(
                        {"address": address["address"], "alias": service["alias"], "illicit": service["illicit"],
                         "owner": service["owner"], "type": service["type"]})
    return services

# Convert the Unix timestamp to DD-MM-YYYY
def unix_to_date(unix_timestamp):
    date_obj = datetime.datetime.fromtimestamp(int(unix_timestamp))
    date_str = date_obj.strftime('%d-%m-%Y')
    return date_str

def get_price(date, currency):
    time.sleep(10) # Avoid CoinGecko's rate limit

    url = f"https://api.coingecko.com/api/v3/coins/banano/history?date={date}&localization=false"
    response = requests.get(url)
    if response.status_code == 429:
        print("CoinGecko rate limit hit. Sleeping for a minute")
        time.sleep(150)
        response = requests.get(url)
    data = response.json()
    try:
        price = data['market_data']['current_price'][currency]
        return price
    except Exception as e:
        print(e)
        return 0


# remember to add aliases
def main():
    with open("statement.csv", 'w', newline='') as statement:
        writer = csv.writer(statement, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Date","Hash", "Type", "Address",
                         "Alias", "Account Type", "Price",
                         "Amount", f"Amount({currency})",
                         "Balance", f"Balance({currency})", "Note"])
        with open(creeperfile, 'r') as export:
            reader = csv.DictReader(export)
            lastdate = ""
            lastprice = ""
            addresses = []
            balance = 0

            # Generate a list of all the accounts in the transaction history
            for row in reader:
                address = row["address"]
                if address not in addresses and address != "":
                    addresses.append(address)

            # Find out if any of the accounts are intermediary accounts
            intermediaries = get_intermediaries(addresses)

            # Find out any services associated with the normal accounts and the intermediaries
            addresses_info = get_services(addresses, intermediaries)

            # Go back to the top of the export file because the last loop went to the bottom
            export.seek(0)
            reader = csv.DictReader(export)

            # Look through the export to get transaction details
            for row in reader:
                tran_type = row["type"]
                if tran_type in ["receive", "send"]:

                    address = row["address"]
                    tran_hash = row["hash"]
                    amount = row["amount"]
                    timestamp = row["timestamp"]

                    # Get additional information about the account if there is any
                    for info in addresses_info:
                        if address == info["address"]:
                            acctype = info["type"]
                            alias = info["alias"]
                            break
                        else:
                            acctype = ""
                            alias = ""

                    # Create a running total of the account balance
                    if tran_type == "receive":
                        balance = balance + float(amount)
                    if tran_type == "send":
                        balance = balance - float(amount)


                    date = unix_to_date(timestamp)
                    # Check if price history exists for the date
                    if timestamp < datetime.datetime(2018, 3, 10):
                        if date == "01-01-1970":
                            print("Unknown timestamp from export")
                        else:
                            print("Timestamp is before CoinGecko's records")
                        price = 0

                    # Get the price of Banano on the date of the transaction
                    else:
                        # The CoinGecko API has a strict rate limit. Ignore making the same request twice.
                        if date != lastdate:
                            try:
                                price = get_price(date, currency=currency)
                            except Exception as e:
                                print(e)
                                time.sleep(60)
                                price = get_price(date, currency=currency)

                        else:
                            price = lastprice
                            print("date is the same")

                    # Calculate the value of the transaction and balance
                    amount_fiat = price * float(amount)
                    balance_fiat = price * float(balance)

                    # Cache the price
                    lastdate = date
                    lastprice = price

                    writer.writerow([date, tran_hash, tran_type, address,
                                     alias, acctype, "{:.2f}".format(price),
                                     amount, "{:.2f}".format(amount_fiat),
                                     "{:.2f}".format(balance),
                                     "{:.2f}".format(balance_fiat)])

main()
