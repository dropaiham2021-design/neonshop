from dataclasses import dataclass

@dataclass
class VatBreakdown:
    net: int      # cents
    vat: int      # cents
    gross: int    # cents
    vat_rate: float

def split_vat_from_gross(gross_cents: int, vat_rate: float) -> VatBreakdown:
    # prices include VAT; compute net = gross / (1+rate)
    net = round(gross_cents / (1 + vat_rate))
    vat = gross_cents - net
    return VatBreakdown(net=net, vat=vat, gross=gross_cents, vat_rate=vat_rate)

def cents(amount: float) -> int:
    return int(round(amount * 100))

def euro(cents_val: int) -> str:
    return f"{cents_val/100:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
