from pydantic import BaseModel


class Number(BaseModel):
    number: int

def plus(a: Number, b: Number) -> Number:
    return Number(number=a.number + b.number)

print(plus(Number(number=1), Number(number=2)))