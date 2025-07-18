from pydantic import BaseModel

LOOKUP: dict = {
    "key": "key",
    "keyr" : "key_r",
    "keyb" : "key_b",
    "keyg" : "key_g"
}

class Item(BaseModel):
    name: str
    type: str
    sprite: str = "" 
    
    
    
#creates a new item, includes name, type and picture id
    def new_item(n: str, t: str):
        item = Item(name = n, type = t)
        item.sprite = get_sprite(n)
        return item
 
#returns the matching sprite from Looup ttable    
def get_sprite(name):
    return LOOKUP[name]

#returns plain key item
def KEY():
    return Item.new_item("key", "key")


