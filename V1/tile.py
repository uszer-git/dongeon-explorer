from pydantic import BaseModel
from pair import Pair
from items import Item
from move import Move
from random import randrange

ACTIVATORS: str = "pl"
RECEIVERS: str = "s"

SPRITES = {
        "#" : (False,   "wall"),
        "." : (True,    "floor"),
        "+" : (True,    "floor_coin"),
        "f" : (False,   "fountain"),
        "e" : (True,    "stairs_down"),
        "su" : (True,   "stairs_up"),
        "p" : (True,    "floor_pressure_plate"),
        "x" : (True,    "trap"),
        "k0" : (True,   "key"),
        "kr" : (True,   "key_r"),
        "kg" : (True,   "key_g"),
        "kb" : (True,   "key_b"),
        "do" : (True,   "open_door"),
        "dc0" : (False, "closed_door"),
        "dcr" : (False, "door_closed_r"),
        "dcg" : (False, "door_closed_g"),
        "dcb" : (False, "door_closed_b"),
        "l1" : (False,  "lever_on"),
        "l0" : (False,  "lever_off"),
        "t" :  (True,   "teleporter"),
        "s00" : (False, "secret_door_11"),
        "s01" : (False, "secret_door_01"),
        "s11" : (True,  "secret_door_11"),
        "s02" : (False, "secret_door_02"),
        "s12" : (False, "secret_door_12"),
        "s22" : (True,  "secret_door_22"),
        "s03" : (False, "secret_door_03"),
        "s13" : (False, "secret_door_13"),
        "s23" : (False, "secret_door_23"),
        "s33" : (True,  "secret_door_33"),   
        "h"   : (True, "potion")
}

#type: str key what type it is (floor, wall etc)
#pos: pair of x and y 
#connected: implement one day to allow for easier across-the-board activation
#moveable: if player can move to tile, determined for now only by type
class Tile(BaseModel):
    type: str
    sprite: str
    pos: Pair
    
    activ_targets: list[Pair] = []
    activ_sources: list[Pair] = []
    
    conn_ID: str
    state: bool
    default_state: bool
    moveable: bool
    
    #creates a new tile of type t, pos p and connected to c
    def new_tile(t: str, p: Pair, c: int,  s: bool):
        spr = get_sprite(t, s, c)
        #if t=="s": print(f"secret door: state {s}, sprite: {spr}")
        return Tile(
            type = t,
            pos = p,
            conn_ID = c,
            default_state = s,
            state = s,
            sprite = spr[1],
            moveable = spr[0]
        )

    #updates tile type
    def change_type(self,game, new_key):
        if len(new_key) == 1:
            self.type = new_key
        else:
            self.type = new_key[0]
            self.conn_ID = new_key[1]
        self.update_tile(game)

    #inverses state
    def activate(self, game):
        if self.is_activator():     #splits logic in two (extra functions? later)
            match self.type:
                case "p":           #pressure platte logic (true as long as anything on it)
                    if game.player.pos.equal(self.pos):
                        self.state = True
                        for targets in self.activ_targets:
                            game.level.get_tile(targets).activate(game)
                    else: self.state = False
                    self.update_tile(game)
                case "l":           #lever logic: toggle on and off
                    #print(f"lever at {self.pos} state: {self.state} activates {self.activ_targets}")
                    self.state = not self.state
                    for targets in self.activ_targets:
                        game.level.get_tile(targets).activate(game)
                    self.update_tile(game)
        elif self.is_receiver:      #receiver logic
            match self.type:
                case "s":           ##secret door
                    #print(f"activators: {self.activ_sources} = {game.level.get_tile(self.activ_sources[0]).state}")
                    for source in self.activ_sources:
                        if not game.level.get_tile(source).state:
                            self.state = self.default_state
                            print(f"{self.type} is missing activator {source}: {game.level.get_tile(source).state}")
                            #print(f"default: {self.default_state}, actual: {self.state}")
                            self.update_tile(game)
                            return
                    self.state = not self.default_state
                    print(f"{self.type} has been activated,{self.default_state} --> {self.state}")
                    self.update_tile(game)
                    return
        else:
            self.state = not self.state
                
    #switch pos of 2 tiles
    def switch_tile(self, other):
        temp: Pair = other.pos
        other.pos = self.pos
        self.pos = temp
    
    #checks if tile is activator
    def is_activator(self):
        return self.type in ACTIVATORS
    #checks if tile is receiver
    def is_receiver(self):
        return self.type in RECEIVERS
    #checks if tile is active (never used lol)
    def is_active(self):
        return self.state
    
    #prints the tile
    def tile_print(self):
        return(f"t: {self.type} at pos (xy): {self.pos.x, self.pos.y}")
     
    #updates the tile sprite to the current state
    def update_tile(self, game):
            #print(f"updating {self.type} at {self.pos.x, self.pos.y} to {self.state}")
            #update sprite
            if self.type == "s":
                sprite = self.secret_door_sprite(game)
                self.sprite = sprite[1]
                self.moveable = sprite[0]
                return
            else:
                sprite = get_sprite(self.type, self.state, self.conn_ID)
            self.sprite = sprite[1]
            self.moveable = sprite[0]
            #update state
            if self.conn_ID != 0 and self.is_receiver():
                for source_pos in self.activ_sources:
                    t = game.level.get_tile(source_pos)
                    if not t.is_active():
                        pass
                        #print(f"Activators are missing: {t.tile_print()}")
                self.state = self.default_state
            #print(f"self is moveable: {self.moveable}, sprite is {self.sprite}")
    
    #get the sprite for secret door from state and number connections
    def secret_door_sprite(self, game):
        #print(f"s at {self.pos} has {len(self.activ_sources)} activators and is in state {self.state}")
        required_activators = len(self.activ_sources)
        activ_activators: int = 0
        if not self.state:      #if not activated->open (all required activators must be open)
            #print(f"{self.pos} is not active, open")
            return SPRITES["s"+str(required_activators)+str(required_activators)]
        
        else:   #return (activ_activators)[of](required_activators)
            for p in self.activ_sources:
                    if game.level.get_tile(p).state: activ_activators+=1
            
            if self.default_state:      #if default closed
                return SPRITES["s"+str(activ_activators)+str(required_activators)]
            else:
                inverted_activators = required_activators-activ_activators
                return SPRITES["s"+str(inverted_activators)+str(required_activators)]
                    
 #get a random direct neigbour    
def random_direct_neighbour(self, tiles: list[Tile], key: str)->Tile:
    possible_tiles: list[Tile] = []
    for rand_tile in tiles:
        #add tiles of type key AND who have only 
        if (rand_tile.type == key and
            (rand_tile.pos.x == self.pos.x or rand_tile.pos.y == self.pos.y) and 
            not rand_tile.pos.equal(self.pos)):
            possible_tiles.append(rand_tile)
    if len(possible_tiles) > 0:
        i = randrange(0, len(possible_tiles))
        #print(f"new tile for door: {possible_tiles[i].type} at {possible_tiles[i].pos}")
        return tiles[i]
    else:
        return None
        
#returns a list of all surrounding tiles
def surrounding_tiles(tile, game)->list[Tile]:
    surrounding_tiles: list[Tile] = []
    start_pos = tile.pos.copy()
    #print(f"start pos: {start_pos}")
    for x in range(start_pos.x-1, start_pos.x+2, 1):
        for y in range (start_pos.y-1, start_pos.y+2, 1):
            pos = Pair.new_pair(y, x)
            surrounding_tiles.append(game.level.get_tile(pos))
    return surrounding_tiles
    
 
#returns the matching sprite
def get_sprite(type, state, conn_ID):
    match type:
        case ".":
            if state: return SPRITES["+"]
            else: return SPRITES["."]
        case "d":
            if state: return SPRITES["do"]
            else: return SPRITES["dc"+conn_ID]
        case "k":
            return SPRITES["k"+conn_ID]
        case "s":
            if state: return SPRITES["#"]
            else: return SPRITES["."]
        case "u":
            if state: return SPRITES["su"]
            else: return SPRITES["."]
        case "l":
            if state: return SPRITES["l1"]
            else: return SPRITES["l0"]
        case _:
            return SPRITES[type]