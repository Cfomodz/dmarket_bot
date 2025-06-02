# dmarket_bot
Bot for automatic trading on dmarket 

## Quick Setup

These instructions will guide you through setting up the `dmarket_bot` using our automated installer scripts. Ensure you have Git and Python 3 installed on your system before proceeding.

---

### For macOS / Linux Users

1.  **Run the Installer:**
    Open your Terminal and execute the following command:
    ```bash
    bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Cfomodz/dmarket_bot/main/installer.sh](https://raw.githubusercontent.com/Cfomodz/dmarket_bot/main/installer.sh))"
    ```
    This command downloads and runs the `installer.sh` script. The script will:
    * Clone the `dmarket_bot` repository from GitHub.
    * Navigate into the cloned `dmarket_bot` directory.
    * Create a Python virtual environment named `venv`.
    * Activate the virtual environment.
    * Install all required Python packages from `requirements.txt`.
    * Create a template `credentials.py` file with placeholder API keys.
    The script will output its progress to the terminal.

2.  **Configure API Keys:**
    Once the installer script is complete:
    * Ensure you are in the `dmarket_bot` directory (the script should leave you there). If not, navigate to it: `cd dmarket_bot`
    * Open the `credentials.py` file using a text editor (e.g., `nano credentials.py`, `vim credentials.py`, or open it with your preferred GUI editor).
    * Inside `credentials.py`, replace `"YOUR_PUBLIC_API_KEY_HERE"` and `"YOUR_SECRET_API_KEY_HERE"` with your actual DMarket Public and Secret API keys respectively. Save the file.

3.  **Run the Bot:**
    After configuring your API keys:
    * Make sure the virtual environment is active (your terminal prompt should typically show `(venv)`). If it's not active, run: `source venv/bin/activate`
    * Execute the main bot script:
        ```bash
        python main.py 
        ```
    
---

### For Windows Users (PowerShell)

1.  **Run the Installer:**
    Open PowerShell (you can search for "PowerShell" in the Start Menu. If you encounter issues, try running PowerShell as Administrator) and execute the following command:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]::Tls11 -bor [System.Net.SecurityProtocolType]::Tls; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('[https://raw.githubusercontent.com/Cfomodz/dmarket_bot/main/installer.ps1](https://raw.githubusercontent.com/Cfomodz/dmarket_bot/main/installer.ps1)'))
    ```
    This command performs several actions:
    * `Set-ExecutionPolicy Bypass -Scope Process -Force;`: Temporarily allows the current PowerShell session to run scripts without being restricted by the execution policy. This change only applies to this specific PowerShell window and session.
    * `[System.Net.ServicePointManager]::SecurityProtocol = ...;`: Ensures that modern TLS security protocols (TLS 1.2, 1.1, 1.0) are enabled for the web request, which helps with downloading from GitHub securely.
    * `Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('...'))`: Downloads the `installer.ps1` script from your GitHub repository and immediately executes it.
    The script will output its progress. It will:
    * Clone the `dmarket_bot` repository.
    * Navigate into the cloned `dmarket_bot` directory.
    * Create a Python virtual environment named `venv`.
    * Attempt to activate the virtual environment (it will provide instructions if manual activation or execution policy changes are needed).
    * Install all required Python packages from `requirements.txt`.
    * Create a template `credentials.py` file with placeholder API keys.
    * The script may pause at the end; press Enter to close its window if it does so when run in a new window.

2.  **Configure API Keys:**
    Once the installer script is complete:
    * Navigate to the `dmarket_bot` directory if you're not already there (e.g., `cd dmarket_bot`). This directory is typically created in your user profile folder (e.g., `C:\Users\YourUserName\dmarket_bot`).
    * Open the `credentials.py` file using a text editor (e.g., Notepad, VS Code, or by typing `notepad credentials.py` in PowerShell while in the `dmarket_bot` directory).
    * Inside `credentials.py`, replace `"YOUR_PUBLIC_API_KEY_HERE"` and `"YOUR_SECRET_API_KEY_HERE"` with your actual DMarket Public and Secret API keys respectively. Save the file.

3.  **Run the Bot:**
    After configuring your API keys:
    * Ensure you are in the `dmarket_bot` directory in PowerShell.
    * Activate the virtual environment if it's not already active (the script attempts this, but if you open a new terminal or it failed, run): `.\venv\Scripts\Activate.ps1`
    * Execute the main bot script:
        ```powershell
        python main.py
        ```


## Features:

- Supports all games available on dmarket.
- Automatic analysis of the skins/items for each game
- Placing orders which are determined by 15 different parameters
- Automatic setting of skins/items for sale after purchase. Adjusting of prices in accordance with the settings.

## Configuration

All configuration parameters are set in the `config.py` file in the root directory of the bot.

### Detailed description of the configuration:

- `logger_config`- logger configuration
```python
logger_config = {
    "handlers": [
        {"sink": sys.stderr, 'colorize': True, 'level': 'INFO'},
        # {"sink": "log/debug.log", "serialize": False, 'level': 'DEBUG'},
        {"sink": "log/info.log", "serialize": False, 'level': 'INFO'},
    ]
}
logger.configure(**logger_config)
```
`"sink": sys.stderr` - output logs to the console
`"sink": "log/info.log"` - output logs to a file
`'level': 'INFO'` is the level of the logs. Possible settings: `TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR , CRITICAL`. Each level from left to right prohibits the output of lower levels. IF the level `INFO` is set messages with the levels `TRACE, DEBUG` won't be displayed.
- `GAMES = [Games.CS, Games.DOTA, Games.RUST]` - a lisit of games that will be used for trading. Available values: `Games.CS, Games.DOTA, Games.RUST, Games.TF2`
- `PREV_BASE = 60 * 60 * 4` - update the skin database every `PREV_BASE` seconds
- `ORDERS_BASE = 60 * 10`- update the order database `ORDERS_BASE` seconds
- `BAD_ITEMS` - a blacklist of words. If the word is included in the name of the item it won't be bought.

### BuyParams - configuration parameters for placing orders
- `STOP_ORDERS_BALANCE = 1000` - Stop placing orders if the balance is <= 10 dollars more than the minimum order price
- `MIN_AVG_PRICE = 400` - The minimum average price for the last 20 purchases of an item in cents. Items with a lower won't be added to the skin database
- `MAX_AVG_PRICE = 3500` - The maximum average price for the last 20 purchases of an item in cents. Items with a higher price will not be added to the skin database. 
- `FREQUENCY = True` - `PROFIT_PERCENT = 6` or less, and the parameter `GOOD_POINTS_PERCENT = 50` or higher.
- `MIN_PRICE = 300` - minimum price. The order won't be placed below this price
- `MAX_PRICE = 3000` - maximum price. The order won't be placed above this price

- `PROFIT_PERCENT = 7` - 
- `GOOD_POINTS_PERCENT = 50` - the minimum percentage of points in the history of the last 20 sales corresponding to the parameter `PROFIT_PERCENT = 7`. In this case, if less than 50 % of points were sold with a profit of less than 7 %, then an order for such a skin/item won't be placed
- `AVG_PRICE_COUNT = 7` - calculating the average price for the last 7 sales to form the estimated profit
- `ALL_SALES = 100` - the minimum number of sales for the entire period, if sales are below this number, the order won't be placed
- `DAYS_COUNT = 20` - at least `SALE_COUNT = 15` sales for `DAYS_COUNT = 20` days. Selection by popularity
- `SALE_COUNT = 15` - at least `SALE_COUNT = 15` sales for `DAYS_COUNT = 20` days. Selection by popularity
- `LAST_SALE = 2` - last sale is no older than LAST_SALE days ago
- `FIRST_SALE = 15` - first purchase is no later than FIRST_SALE days ago

- `MAX_COUNT_SELL_OFFERS = 30` - The maximum number of items for sale. Above 30 the order won't be placed

- `BOOST_PERCENT = 24` - remove up to 3 points that are 24 % higher than average price
- `BOOST_POINTS = 3` - remove up to 3 points that are 24 % higher than average price

- `MAX_THRESHOLD = 1` - the maximum price increase by MAX_THRESHOLD in % of the current order. The maximum increase in the price of your order from the price of the current first order
- `MIN_THRESHOLD = 3` - the maximum decrease in the price of your order from the price of the current one. Sets the price change boundaries for the order

### SellParams - configuration parameters for selling
- `MIN_PERCENT = 7` - minimum profit percentage
- `MAX_PERCENT = 15` - maximum profit percentage
