from pydantic import BaseModel#
from pair import Pair
from items import Item

LOOKUP_SPRITE = {
    "r" : "rat",
    "o" : "fireball",
}

class entity(BaseModel):
    type: str
    sprite: str
    name: str
    pos: Pair
    move: Pair
    drop: Item
    hp: int
    damage: int = 1
    
    
    def new_entity(game, t: str, n:str, p:Pair, d: Item):
        #if spawn on illegal tile, return None
        if not game.level.get_tile(p).moveable:
            return None
        health = get_hp_from_type(t)
        return entity(
            type=t,
            name=n,
            pos=p, 
            drop=d,
            hp=health
        )
    
    def update_entity(self):
        match self.type:
            case "r":
                self.rat()
            case "o":
                self.fireball()
                
    
    def rat():
        pass


    def fireball():
        pass

def get_hp_from_type(type):
    match type:
        case "rat":
            return 3
        case "fireball":
            return 1
        
    