#!/usr/bin/python
from datetime import datetime
from bs4 import BeautifulSoup
import asyncio
import httpx
from enum import Enum
from dotenv import load_dotenv

from db import check_duplicate, check_error, make_db_client

from schemas.ad import Ad, Info, Price
from schemas.job import JobResponse, create_default_job, Job

load_dotenv()


database = make_db_client()


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


def convert_to_datetime(date_str) -> datetime | None:
    try:
        if '/' in date_str:
            return datetime.strptime(date_str, '%Y/%m')
        else:
            return datetime.strptime(date_str, '%Y')
    except ValueError:
        return None  # Return None if the conversion fails

def try_float(n: str) -> float | None:
    try:
        return float(n)
    except:
        return None

def try_int(n: str) -> int | None:
    try:
        return int(n)
    except:
        return None

async def make_ad_from_page(link: str, client: httpx.AsyncClient) -> Ad: 

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

    reg = get_attr(soup, "Reg. Year/Month")
    milage = get_attr(soup, "Mileage").replace(' KM' , '').replace(',','')
    doors = get_attr(soup, "Doors").replace('Doors', '')
    cc = get_attr(soup, "Engine CC").replace(' CC', '').replace(',','')
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
    price = (price.find("span").find("strong").text if price != None else "0") # type: ignore
    price = price.replace(',','')

    return Ad(
        Price(
            try_float(price),
            0,
            str(currency)),
        link,
        Info(
            convert_to_datetime(reg),
            try_int(milage),
            try_int(cc),
            transmission,
            steering,
            fuel,
            try_int(doors),
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

async def write_ad(job:JobResponse, link: str, client: httpx.AsyncClient, dry_run: bool = True):
    ad = await make_ad_from_page(link, client)
    add = ad.to_dict()
    add['from_job'] = job.id

    if not dry_run and database != None:
        try:
            r = await database.from_("ads").insert(add).execute()

            if check_duplicate(r):
                job.duplicates += 1

            if check_error(r):
                job.ads_failed_to_create += 1

            else:
                job.total_ads_created += 1
        except Exception as e:
            print(e)

async def get_cars(job: JobResponse, brand: BrandEnum, model: ModelEnum):

    print('starting...', brand, model)

    tasks = []

    async with httpx.AsyncClient() as client:
        for n in range(70):
            url = baseurl + build_url(brand.value, model.value, pages(n))
            client.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

            for link in await get_links(url, client):
                tasks.append(write_ad(job, link, client, False))


        print('Ready, Set, Go!')
        await asyncio.gather(*tasks)

async def main():
    tasks = []

    default_job = create_default_job()
    job = JobResponse(**(await database.from_("jobs").insert(default_job.to_dict()).execute()).data[0])

    tasks.append(get_cars(job, BrandEnum.AUDI,     ModelEnum.A_A4))
    tasks.append(get_cars(job, BrandEnum.HONDA,    ModelEnum.H_Accord))
    tasks.append(get_cars(job, BrandEnum.NISSAN,   ModelEnum.N_Note))
    tasks.append(get_cars(job, BrandEnum.NISSAN,   ModelEnum.N_Silvia))
    tasks.append(get_cars(job, BrandEnum.NISSAN,   ModelEnum.N_GTR))
    tasks.append(get_cars(job, BrandEnum.NISSAN,   ModelEnum.N_Leaf))
    tasks.append(get_cars(job, BrandEnum.TOYOTA,   ModelEnum.T_Celica))
    tasks.append(get_cars(job, BrandEnum.BMW,      ModelEnum.B_X5))
    tasks.append(get_cars(job, BrandEnum.FORD,     ModelEnum.F_Explorer))
    tasks.append(get_cars(job, BrandEnum.MERCEDES, ModelEnum.M_G_class))

    await asyncio.gather(*tasks)
    await database.from_("jobs").update(job.to_dict()).eq("id", job.id).execute()

if __name__ == "__main__":
    asyncio.run(main())
