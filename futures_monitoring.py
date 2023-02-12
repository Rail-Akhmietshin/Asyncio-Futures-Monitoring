import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time


headers = {
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 YaBrowser/23.1.1.1138 Yowser/2.5 Safari/537.36"
}

pages = 4

class CheckDynamicRate:
    __values = { "count_pages" : 0 }
   
    def __init__(self, new_rates: dict) -> None:
        if self.__values["count_pages"] < pages:
            self.__values |= new_rates
            self.__values["count_pages"] += 1
        self.__dict__ = self.__values

    def get_rate(self, item: str) -> str:
        return self.__values.get(item, 1)
    
    def update_rate(self, key: str, value: str) -> None:
        self.__values[key] = value



while True:
    start = time.monotonic()

    async def check_dynamic_rate(new_rates: dict) -> None:
        rates = CheckDynamicRate(new_rates)
        for key in new_rates:
            current_value, new_value = map(float, (rates.get_rate(key), new_rates.get(key, 1)))

            different_values = round(current_value / new_value, 2)

            if (different_values > 1) and (current_value * 0.99 > new_value or current_value * 1.01 < new_value):
                print(f"Фьючерс {key} изменился более, чем на {different_values}%. {current_value} >> {new_value}")
                rates.update_rate(key, new_value)
    
    async def get_rates(session, url: str) -> None:
        async with session.get(url, timeout=None) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'lxml')
            name_rate = []
            for x in soup.find_all("div", class_="css-1v05rmn"):
                value = x.text.replace("USD", " / USD") if x.text.endswith("USD") else x.text.replace("USDT", " / USDT")
                name_rate.append(value)
            rate = [x.text.replace(u'\xa0', u'').replace(",", ".").split("/")[0] for x in soup.find_all("div", class_="css-1r1yofv")]

            actual_rates = dict(list(zip(name_rate, rate)))
            await check_dynamic_rate(actual_rates)

    async def main() -> None:
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            for number in range(1, 5):
                url = f'https://www.binance.com/ru/markets/futures?p={number}'
                tasks.append(asyncio.ensure_future(get_rates(session, url)))
            await asyncio.gather(*tasks)
        await session.close()

    asyncio.run(main())

    print(f"\nВремя обработки и вывода данных в консоль: {time.monotonic() - start}")
    print("Повторное обновление данных произойдёт через 10 секунд\n\n")

    time.sleep(10)
