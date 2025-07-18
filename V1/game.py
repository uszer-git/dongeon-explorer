"""
the Dungeon Explorer game logic
"""
import random
from pydantic import BaseModel
from move import Move
from pair import Pair
from items import Item
from player import Player
from tile import Tile
from level import Level
import sys

class DungeonGame(BaseModel):
    status: str = "running"
    player: Player       
      
    moves: list[Move] = []
    level: Level
    old_levels: list[Level] = []
    
    show_lines: bool = True
    text: list[dict] = []
    lines: list[dict] = []

#broken random scatter when touching traps, rewrite for new Level-Tile-Pair system

#returns a random floor tiles position as a pair in a radius around the input x,y  
#also allows for random teleportation when inputing large values :)       
    def random_scatter(self, pos:Pair, scatter_radius)->Tile:
        #print(f"scattering around (x,y) {pos} inf {scatter_radius} radius")
        #create list of coordinate pairs (9 for all surrounding tiles)
        spaces: list[Tile] = []
        
        #iterate through all surrounding tiles (make sure its inbound!)
        
        for x in range (pos.x-scatter_radius, pos.x+1+scatter_radius):
            for y in range (pos.y-scatter_radius, pos.y+1+scatter_radius):
                #only if inside of the level: len(row) and len(collom)
                if (x<self.level.width and y<self.level.height and x>= 0 and y >= 0):
                    #append copy of current tile 
                    t = self.level.get_tile(Pair.new_pair(y, x)).model_copy()
                    #checks for exit markers
                    for e in self.level.exit_markers:
                        if t.pos.equal(e[0]):
                            break
                    else:
                        spaces.append(t)
        
        #choose random floor from spaces (surrounding pos)
        for x in range(100):
            random_space = random.choice(spaces)
                
            #if random space is not the players position
            if not random_space.pos.equal(self.player.pos):                    
                #if it is floor, move there
                if random_space.type == ".":
                    return random_space
                #if it is door, check if open (state high)
                elif random_space.type == "d" and random_space.state :
                    return random_space
                #if it is gate (secret door), check if open (state low)
                elif random_space.type == "s" and not random_space.state:
                    return random_space
                
        raise TimeoutError(f"Scattering timeout around {pos}")
    
    def update(self, move):
        self.player.move_player(self, move)
     
     
     #ISSUE: game crashes randomly without error
    
    #generates the next level and stores the old one to keep level states
    def next_level(self, next):
        nextID = next[1]
        nextSpawn = next[2]
        print(f"new room: {self.level.ID} to {nextID}", end = " ")

        #check if level in old, already loaded levels
        for l in self.old_levels:                   #check through all already played levels          
            if nextID == l.ID:               #if next level has already been played 
                print("loading from old levels")
                self.old_levels.append(self.level)  #add current level to old levels
                self.level = l                      #update current level to next level
                self.old_levels.remove(l)           #remove now current level from the list
                self.player.place_player(self, nextSpawn)
                for t in self.level.lvl:
                    t.update_tile(self)
                return        
                                                                       
        #if next level is a new level    
        print("loading new room")
        self.old_levels.append(self.level)      #store current level in old levels
        self.level = Level.new_level(nextID)   #create the new level and store it in the current level
        #print(f"Placing player at new spawn: {nextSpawn}")
        self.player.place_player(self, nextSpawn)  
        for t in self.level.lvl:
            t.update_tile(self)    
        for l in self.old_levels:
            print(f"[{l.ID}] ", end = "")
        
  
        
def start_game(ID):
    
    random.seed()
    lvl: Level = Level.new_level(ID)
    pl: Player = Player.new_player(lvl.spawn.model_copy())
    game = DungeonGame(
        player = pl,
        level=lvl,  
        )
    #game.text.append({"t" : "Game started", "s" : 500, "c" : (255, 255, 255)})
    return game
