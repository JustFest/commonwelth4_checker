import asyncio
import aiohttp
import random
import json
import time
import pandas as pd
import aiofiles
from logger_setup import get_logger
from tqdm import tqdm
import os

logger = get_logger()

# Завантаження конфігураційного файлу
def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"Конфігурацію завантажено з {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"Файл конфігурації {config_file} не знайдено")
        return {}

# Завантажуємо гаманці з файлу
async def load_addresses(file_path):
    if not os.path.exists(file_path):
        logger.error(f"Файл з адресами {file_path} не знайдено")
        return []
    async with aiofiles.open(file_path, 'r') as f:
        addresses = [line.strip() for line in await f.readlines()]
    logger.info(f"Завантажено {len(addresses)} адрес з файлу {file_path}")
    return addresses

# Завантажуємо проксі з файлу
async def load_proxies(file_path):
    if not os.path.exists(file_path):
        logger.error(f"Файл з проксі {file_path} не знайдено")
        return []
    async with aiofiles.open(file_path, 'r') as f:
        proxies = [line.strip() for line in await f.readlines()]
    logger.info(f"Завантажено {len(proxies)} проксі з файлу {file_path}")
    return proxies

# Асинхронний запит балансу для одного гаманця
async def get_balance(session, address, proxy, index, total, semaphore, api_base_url):
    url = f'{api_base_url}{address}'
    max_retries = 3
    retry_delay = 5
    start_time = time.time()

    async with semaphore:
        for attempt in range(max_retries):
            try:
                logger.debug(f"[{index+1}/{total}] Спроба {attempt + 1} запиту балансу для адреси {address}")
                async with session.get(url, proxy=proxy, timeout=20) as response:
                    response.raise_for_status()
                    data = await response.json()
                    balance = data["data"].get("balance")
                    claim = data["data"].get("claim")
                    elapsed_time = time.time() - start_time
                    logger.success(f"[{index+1}/{total}] Успішно отримано баланс для адреси {address}: {balance}, claim: {claim}, Час: {elapsed_time:.2f} секунд")
                    return address, balance, claim
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"[{index+1}/{total}] Помилка запиту для адреси {address}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"[{index+1}/{total}] Повторна спроба через {retry_delay} секунд...")
                    await asyncio.sleep(retry_delay)
                else:
                    elapsed_time = time.time() - start_time
                    logger.error(f"[{index+1}/{total}] Досягнуто максимальну кількість спроб для адреси {address}. Час: {elapsed_time:.2f} секунд")
                    return address, None, None

# Збереження результатів у Excel
def save_balances_to_excel(data, filename):
    try:
        df = pd.DataFrame(data, columns=["Wallet", "Balance", "Claim"])
        df.to_excel(filename, index=False)
        logger.success(f"Результати збережено у файл {filename}")
    except Exception as e:
        logger.error(f"Помилка при збереженні результатів у Excel: {e}")

async def main():
    config = load_config()

    # Завантажуємо параметри з конфігу
    max_concurrent_requests = config.get("max_concurrent_requests", 10)
    addresses_file = config.get("addresses_file", "addresses.txt")
    proxies_file = config.get("proxies_file", "proxies.txt")
    output_file = config.get("output_file", "commonwealth_checker.xlsx")
    api_base_url = config.get("api_base_url", "https://api.commonwealth4.com/airdrop_balance?user=")

    addresses = await load_addresses(addresses_file)
    proxies = await load_proxies(proxies_file)
    results = []
    total_addresses = len(addresses)

    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, address in enumerate(addresses):
            proxy = f'http://{random.choice(proxies)}'
            task = asyncio.create_task(get_balance(session, address, proxy, index, total_addresses, semaphore, api_base_url))
            tasks.append(task)

        for completed_task in tqdm(asyncio.as_completed(tasks), total=total_addresses, desc="Processing wallets"):
            address, balance, claim = await completed_task
            if balance is not None:
                results.append((address, balance, claim))

    save_balances_to_excel(results, output_file)

if __name__ == "__main__":
    logger.info("Початок роботи скрипта")
    asyncio.run(main())
    logger.info("Завершення роботи скрипта")
