from fastapi.templating import Jinja2Templates
import random

backgrounds = [
    "bg_1.png",
    "bg_2.png",
    "bg_3.png",
]

def random_background():
    return random.choice(backgrounds)

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["random_background"] = random_background
