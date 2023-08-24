#!/usr/bin/python

from bs4 import BeautifulSoup
from dataclasses import dataclass
import csv
import asyncio
import httpx
from enum import Enum

class BrandEnum(Enum):
    AUDI = 'audi-26'
    HONDA = 'honda-3'
    NISSAN = 'nissan-2'
    MITSUBISHI = 'mitsubishi-4'
    TOYOTA = 'toyota-1'
    FORD = 'ford-16'
    BMW = 'bmw-23'
    MERCEDES = 'mercedes-128'

class ModelEnum(Enum):
    A_A4 = 'a4-375'
    H_Accord = 'accord-710'
    N_Note = 'note-277'
    N_Silvia = 'silvia-306'
    M_Lancer = 'lancer-1061'
    T_Celica = 'celica-27'
    F_Explorer = 'explorer-605'
    N_Leaf = 'leaf-22538'
    N_GTR = 'gtr-1843'
    M_G_class = 'g+class-2718'
    B_X5 = 'x5-429'

fieldnames = {
    "FOB", "CIF", "currency",
    "make", "model", 
    "reg", "milage", "cc", "transmission", "steering", "fuel", "doors",
    "url"
}

@dataclass
class Price:
    FOB: str
    CIF: float 
    currency: str

@dataclass
class Info:
    reg: str
    mileage: str
    cc: str
    transmission: str 
    steering: str
    fuel: str
    doors: str
    make: str
    model: str

@dataclass
class CarAd:
    price: Price
    url: str
    info: Info

    def to_dict(self):
        return {
        "FOB": self.price.FOB,
        "CIF": self.price.CIF,
        "make": self.info.make,
        "model": self.info.model,
        "currency": self.price.currency,
        "reg": self.info.reg,
        "milage": self.info.mileage,
        "cc": self.info.cc,
        "transmission": self.info.transmission,
        "steering": self.info.steering,
        "fuel": self.info.fuel,
        "doors": self.info.doors,
        "url": self.url
        }


async def make_ad_from_page(link: str, client: httpx.AsyncClient) -> CarAd: 

    def get_attr(soup: BeautifulSoup, attr: str):
        element = soup.find("span", attrs = {"aria-label": attr})
        if element:
            div = element.parent
            if div:
                return div.get_text()
        return ""

    response = await client.get(link, timeout=None)
    soup = BeautifulSoup(response.text, "html.parser")

    currency = "USD"

    # this doesnt work be cause javascript is too slow omegalul
    # options = soup.find_all("option")
    # for option in options:
    #     if option.has_attr('selected'):
    #         print("found currency")
    #         currency = option.get_text()

    reg = get_attr(soup, "Reg. Year/Month")
    milage = get_attr(soup, "Mileage")
    doors = get_attr(soup, "Doors")
    cc = get_attr(soup, "Engine CC")
    transmission = get_attr(soup, "Transmission")
    steering = get_attr(soup, "Steering")
    fuel = get_attr(soup, "Fuel")
    spans = soup.find_all('span')
    make, model = None, None

    for entry in spans:
        if entry.get_text() == "Make":
            make = entry.parent.find('strong').get_text()
        if entry.get_text() == "Model":
            model = entry.parent.find('strong').get_text()

    price = soup.find("div", class_="fob_price")
    price = (price.find("span").find("strong").text if price != None else "0")

    return CarAd(
        Price(
            price, 
            0, 
            str(currency)),
        link,
        Info(
            reg, 
            milage, 
            cc, 
            transmission, 
            steering, 
            fuel, 
            doors, 
            str(make), 
            str(model)
        )
    )

def pages(n: int) -> str:
    if n < 2:
        return ""

    return f"p{n}"

baseurl = "https://www.japanesecartrade.com/make-model/"

def build_url(brand: str, model: str, page: str):
    if page:
        return f"{brand}-{model}-{page}.html"
    return f"{brand}-{model}.html"

async def get_links(url: str, client: httpx.AsyncClient):
    links = []
    response = await client.get(url, timeout=None)

    soup = BeautifulSoup(response.text, "html.parser")

    header2s = soup.find_all('h2', class_="list_head")
    for header in header2s:
        links.append(header.find('a').get('href'))

    return links

async def write_ad(link: str, client: httpx.AsyncClient, writer: csv.DictWriter):
    ad = await make_ad_from_page(link, client)
    print(f"Reading {link}")
    writer.writerow(ad.to_dict())


async def get_cars(writer: csv.DictWriter, brand: BrandEnum, model: ModelEnum):

    print('starting...', brand, model)

    tasks = []

    async with httpx.AsyncClient() as client:
        for n in range(70):
            url = baseurl + build_url(brand.value, model.value, pages(n))
            client.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

            for link in await get_links(url, client):
                tasks.append(write_ad(link, client, writer))


        print('Ready, Set, Go!')
        await asyncio.gather(*tasks)        

async def main(file):
    tasks = []

    tasks.append(get_cars(file, BrandEnum.AUDI, ModelEnum.A_A4))
    tasks.append(get_cars(file, BrandEnum.HONDA, ModelEnum.H_Accord))
    tasks.append(get_cars(file, BrandEnum.NISSAN, ModelEnum.N_Note))
    tasks.append(get_cars(file, BrandEnum.NISSAN, ModelEnum.N_Silvia))
    tasks.append(get_cars(file, BrandEnum.NISSAN, ModelEnum.N_GTR))
    tasks.append(get_cars(file, BrandEnum.NISSAN, ModelEnum.N_Leaf))
    tasks.append(get_cars(file, BrandEnum.TOYOTA, ModelEnum.T_Celica))
    tasks.append(get_cars(file, BrandEnum.BMW, ModelEnum.B_X5))
    tasks.append(get_cars(file, BrandEnum.FORD, ModelEnum.F_Explorer))
    tasks.append(get_cars(file, BrandEnum.MERCEDES, ModelEnum.M_G_class))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    with open("data.csv", "+w") as file:
        writer = csv.DictWriter(file, fieldnames)
        writer.writeheader()
        asyncio.run(main(writer))