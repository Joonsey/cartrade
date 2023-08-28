from dataclasses import dataclass
from datetime import datetime

@dataclass
class Price:
    FOB: float | None
    CIF: float | None
    currency: str

@dataclass
class Info:
    reg: datetime | None
    mileage: int | None
    cc: int | None
    transmission: str
    steering: str
    fuel: str
    doors: int | None
    make: str
    model: str

@dataclass
class Ad:
    price: Price
    url: str
    info: Info
    created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
        "created_at" : self.created_at,
        "fob": int(self.price.FOB) if self.price.FOB != None else None,
        "cif": int(self.price.CIF) if self.price.CIF != None else None,
        "make": self.info.make,
        "model": self.info.model,
        "currency": self.price.currency,
        "registered": (self.info.reg.isoformat() if self.info.reg != None else None),
        "mileage": self.info.mileage,
        "cc": self.info.cc,
        "transmission": self.info.transmission,
        "steering": self.info.steering,
        "fuel": self.info.fuel,
        "doors": self.info.doors,
        "url": self.url,
        }