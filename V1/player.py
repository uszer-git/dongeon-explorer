from pair import Pair
from items import Item
from pydantic import BaseModel
from move import Move, player_update_pos, player_next_move
from tile import Tile
from functools import partial
import random

FOUNTAIN = {
    "r" : "kr",
    "g" : "kg",
    "b" : "kb",
    "h" : "hp",   
}

FOUNTAIN_ITEMS = {
    "r" : ("red key", (0, 0, 255)),
    "g" : ("green key",(0, 255, 0)),
    "b" : ("blue key",(255, 0, 0)),
    "h" : ("health potion",(128, 128, 128))   
}



class Player(BaseModel):
    pos: Pair
    inv: list[Item] = []
    
    max_hp: int = 5
    hp: int = 3
    speed: int = 2
    coins: int = 0
    
    ghost: bool = False
    
    #creates a new player at position
    def new_player(position: Pair):
        return Player(
            pos = position
        )
     
    #initiates player move
    def move_player(self, game, direction: str) -> None:
        if direction:               #only if direction is not null-->actual input
            next: Pair = Pair.new_pair(self.pos.y, self.pos.x)
            match direction:
                case "right":
                    next.x += 1
                case "left":
                    next.x -= 1
                case "up":
                    next.y -= 1
                case "down":
                    next.y += 1
                case "fireball" :
                    self.toggle_combat_stance()
                    return
                    
            self.check_next_player_loc(game, next)
            #print("\n")
            
        self.check_player_loc(game)  
 
    #does a smooth player move from current player pos to input, uses global player speed       
    def playerDoMove(self, game, next: Pair):
        if self.pos.equal(next):
            raise Exception(f"player at {self.pos} cannot move to {next} because they are equal")
        #moveable tile ahead 
        f = partial(player_update_pos, next = next)      
        move = Move(tile = "player",                                #what to move (tile where player is rendered)
                    from_x =self.pos.x, from_y = self.pos.y,                #from current location
                    speed_x=self.speed*(next.x-self.pos.x),       #speed is spacial difference
                    speed_y=self.speed*(next.y-self.pos.y),
                    finished=f
                    )     
        if game.level.check_tile(self.pos, "p"):
            pass
        #game cords updated by player_update_pos
        #actually perform move
        game.moves.append(move)
                 
    #teleports the player to the input pair w/o animation 
    def place_player(self, game, new:Pair):
        if new.x<game.level.width or new.y<game.level.height:
            self.pos.x = new.x
            self.pos.y = new.y
        else:
            raise IndexError("Coordinates (x,y)", new.x, new.y, "are outside the defined area") 
     
         #checks the tile the player is on rn (traps, pressure plates, coins etc) 
    
    #checks the tile the player is on rn (coins, pressure plates, exits etc)
    def check_player_loc(self, game):
        t: Tile = game.level.get_tile(self.pos)
        #handle exits
        for e in game.level.exit_markers:
            if self.pos.equal(e[0]):
                game.next_level(e)
                return
        #handle special tiles
        match t.type:
            case "e":   #exit
                print("Game finished")
                pass
            case ".":   #floor: if active, add coin
                if t.state: 
                    game.text.append({"t": "This gold looks cursed. Better leave it untouched!", "s": 300, "c": (255, 255, 255)})
                    t.state = not t.state
            case "p":   #pressure plate, change state of every other tile connected
                t.activate(game)
                #print(f"pressing {t.pos.x, t.pos.y}: activating {t.activ_targets} ")
            case "+":
                #print("Coin collected")
                game.text.append({"t": "You picked up some Gold!", "s" : 300, "c": (10, 140, 230)})
                game.level.set_tile(game, self.pos, ".")
                self.coins += 1
            case "x":
                #print("walked into trap")
                self.place_player(game, game.random_scatter(self.pos, 1).pos)
                #random scatter in place player after fix
                self.player_change_hp(game, change=-1)
            case "k":
                self.inv.append(Item.new_item("key"+t.conn_ID, "key"))
                game.level.set_tile(game, self.pos, ".") 
                match t.conn_ID:
                    case "r":
                        game.text.append({"t" : "Picked up a red Key!", "s" : 500, "c" : (0, 0, 255)})                    
                    case "g":
                        game.text.append({"t" : "Picked up a green Key!", "s" : 500, "c" : (0, 255, 0)})                                            
                    case "b":
                        game.text.append({"t" : "Picked up a blue Key!", "s" : 500, "c" : (255, 0, 0)})                    
            case "h":
                self.hp = self.max_hp
                t.update_tile(game)
    
    #checks the location the player will be on next turn (doors, fountains, interactable objects, enemies?)
    def check_next_player_loc(self, game, next: Pair):
        #print(f"Next tile at {next.x, next.y} is {game.level.get_tile(next).type}")
        t: Tile = game.level.get_tile(next)
        
        #if moveable, move on it
        if game.level.get_tile(next).moveable or self.ghost:
            self.playerDoMove(game, next)
            return
        else: 
            #print(f"next {next.x, next.y} is not moveable: type '{game.level.get_tile(next).sprite}'")
            pass
        
        #else, interact
        match t.type:
            case "d":   #door handling
                print(f"door: state {t.state}, sprite {t.sprite}")

                if not t.state: #only if door state is false == closed
                    k = Item.new_item("key"+t.conn_ID, "key")
                    if k in self.inv:   #if player posesses matching key, open door and remove key
                        t.state = True
                        self.inv.remove(k)
                        t.update_tile(game)
                        used = FOUNTAIN_ITEMS[t.conn_ID]
                        text = f"You used a {used[0]} to open the door!"
                        color = used[1]
                        game.text.append({"t":text, "s": 300, "c": color})
                        print(f"{t.conn_ID} door opened: {t.state}")
                    else:               #if not, inform player about key
                        needed= FOUNTAIN_ITEMS[t.conn_ID]
                        text = "You need a "+needed[0]
                        color = needed[1]
                        game.text.append({"t" : text, "s" : 500, "c" : color})                    
   
            case "l":   #lever handling
                if t.state:
                    game.text.append({"t" : "Lever deactivated!", "s": 300, "c" : (0, 0, 255)})
                    game.lines.append({"p1" : t.pos, "p2": t.activ_targets, "s" : 200, "c" : (0, 0, 255)})

                else:
                    game.text.append({"t" : "Lever activated!", "s": 300, "c" : (0, 255, 0)})
                    game.lines.append({"p1" : t.pos, "p2": t.activ_targets, "s" : 200, "c" : (0, 255, 0)})                      
                t.activate(game)        
            case "f":   #fountain handling
                if not t.state:
                    game.text.append({"t": "This fountain seems to have lost its power", "s": 400, "c" : (255, 255, 255)})
                elif self.coins < 1:
                    game.text.append({"t": "You search through your pockets, but find none.", "s": 600, "c": (10, 140, 200)})
                    game.text.append({"t": "You can see coins lying in the fountain", "s": 600, "c": (10, 140, 200)}) 
                elif t.state and self.coins > 0:
                    game.text.append({"t": "You toss a coin into the water!", "s" : 400, "c": (10, 140, 200)})
                    self.interact_fountain(game, t)
                    self.coins-=1
                    t.state = False
            case "s":
                signals = list(t.sprite)[-1]
                if signals == "1":
                    signals += " signal"
                else:
                    signals += " signals"
                text = f"The Gate is locked. It seems to need {signals} to open"
                game.text.append({"t": text, "s": 300, "c": (255, 255, 255)})
        
    def interact_fountain(self, game, fountain):
        match fountain.conn_ID:
            case "d":
                self.player_change_hp(game, -1, True)
                print(f"taking damage")
            case "p":
                target_pos = random.choice(game.level.exit_markers)[0]
                current_pos = self.pos
                self.ghost = True
                player_next_move(game= game, target=target_pos, current=current_pos, )
            case "c":
                print(f"You got hit by the curse of the fountain")
                #hide health bar?
                pass
            case "z":
                r = random.choice("dpcn")
                fountain.conn_ID = r
                self.interact_fountain(game, fountain)
            case "n":
                print("nothing happens")
                return
            case _:
                try: 
                    place = game.random_scatter(pos=fountain.pos, scatter_radius = 1)
                except:
                    try:
                        place = game.random_scatter(pos = fountain.pos, scatter_radius = 2)
                    except: 
                        print(f"Something went wrong while trying to scatter around {fountain.pos}")
                else:
                    game.level.set_tile(game, place.pos, FOUNTAIN[fountain.conn_ID])
                    text = "The fountain spits out a "+FOUNTAIN_ITEMS[fountain.conn_ID][0]
                    color = FOUNTAIN_ITEMS[fountain.conn_ID][1]
                    game.text.append({"t": text, "s": 300, "c": color})
                        

    #changes the player hp by the input changed (+ and -), if 0 do something, caps at max hp if enabled
    def player_change_hp(self, game, change):
        self.hp += change
        if self.hp < 1:
            game.status = "game over"
              