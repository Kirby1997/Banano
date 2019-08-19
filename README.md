# Banano Toolbox by Kirby

All the applications in this pack are written in Python 3.7  
All dependencies are inside "requirements.txt". Windows users can run "setup.bat" to install all dependencies automatically

## SendMulti.py
SendMulti.py is a tool for "raining" evenly across addresses inside of "addresses.txt" (addresses separated by new lines).
The node used can be changed within the file SendMulti.py. By default it uses the official public Banano API. The tool 
supports raining from a disposable address or a vanity address by importing a seed. Wallets are destroyed upon completion
of sending and extra Banano can be returned. This tool will rain all the Banano in a wallet so ensure it only contains 
what you want to distribute.  

The dependencies are:    
aiohttp  
asyncio  
json  
aiofiles  
bitstring  
validations.py

## TotalTo.py 
TotalTo.py is a tool for calculating the total amount of Banano a Banano address has sent to each address in its 
transaction history.  

The dependencies are:  
asyncio  
aiohttp  
json

## DiscordHunter.py
DiscordHunter.py is a tool for identifying what Discord addresses a Banano address has links with. This is useful for 
identifying alternative accounts.  

The dependencies are:  
asyncio  
aiohttp  
json

## ExchangeFinder.py 
ExchangeFinder.py is a tool for identifying the intermediaries. It imports the "exchanges.txt" file, a colon separated 
list of exchanges, gambling sites and aliases. The tool works by identifying whether an address sends Banano to an address
which sends its Banano to an address in the list.  

The dependencies are: 
asyncio  
aiohttp  
json  
aiofiles 
  
Donations can be sent to: ban_1kirby19w89i35yenyesnz7zqdyguzdb3e819dxrhdegdnsaphzeug39ntxj
