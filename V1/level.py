import os
from pydantic import BaseModel
from tile import Tile
from pair import Pair
from typing import Final
import sys

LEVEL_PATH = os.path.split(__file__)[0]

class Level(BaseModel):
    ID: int
    lvl: list[Tile]
    spawn: Pair
    exit_markers: list[tuple[Pair, int, Pair]]
    width: int
    height: int
        
    def new_level(levelID: int):
        level, exits = tile_from_file(levelID)
        #returns 
        #print_level(level)
        sp : Pair = Level.get_location(level, "u")
        if sp.empty():
            sp = Level.get_location(level, ".")
        
        
        new_level = Level(
            ID = levelID,
            lvl = level,
            spawn = sp,
            exit_markers = exits,
            width = level_get_width(level),
            height = level_get_height(level)
        )
        return new_level

    #returns the tile on the position loc(action) 
    #to use: game.level.get_tile(Pair)->Tile
    def get_tile(self, loc: Pair)->Tile:
        for t in self.lvl:
            if t.pos.equal(loc):
                return t
            
    #input location as Pair and the new key, updates tile
    #game.level.set_tile(Pair, str)->None
    def set_tile(self, game, loc: Pair, new_key: str)->None:
        for t in self.lvl:
            if t.pos.equal(loc):
                t.change_type( game, new_key=new_key)          
      
    #returns whether the type at input position is key
    def check_tile(self, loc:Pair, key: str)->bool:
        return self.get_tile(loc).type == key   
        
    #changes the state of a tile
    def change_tile_state(self, game, loc: Pair, change: bool):
        t = self.get_tile(loc)
        t.state = change
        t.update_tile(game)
        
    #finds FIRST tile of type key in the tile array 
    #suppprted input: list[tile], Level
    #returns the coordinates as a pair or empty pair if not found
    def get_location(self, key: str)->Pair:
        #if Level-type: call again with lvl Tile list and return that
        #keys: list[Pair] = []
        if type(self) == Level:
            return Level.get_location(self.lvl, key=key)
        elif type(self == list) and self:
            if type(self[0]) == Tile:
                t: Tile
                for t in self:
                    if t.type == key:
                        return t.pos.copy()
                        #keys.append(t.pos.copy())
                #if key not found, return empty pair
                return Pair.new_empty_pair()
        #else, invalid type input
        else:
            raise TypeError("Invalid type input in get_location: supported types are list[Tile], list[list[str]] (not empty) and Level") 
        
#returns int width (length of string in second dimension list), input level ID
def level_get_width(lvl: list[Tile])->int:
    max_x = 0
    for t in lvl:
        if t.pos.x > max_x:
            max_x = t.pos.x
            
    return max_x

#returns int height (number of second dimension list), input level ID
def level_get_height(lvl: list[Tile])->int:
    max_y = 0
    for t in lvl:
        if t.pos.y > max_y:
            max_y = t.pos.y
            
    return max_y

#prints the level (input any level type) (rewrite to reduce input to list[list[str]])
def print_level(input):
    string: list[list[str]]
    output: str = ""
    
    if type(input) == list and input:
        if type(input[0]) == Tile:
            last_y = input[0].pos.y
            for t in input:
                if not t:
                    raise ValueError(f"t in input {t} is not valid somehow")
                if t.pos.y > last_y:
                    output +="\n"
                    last_y = t.pos.y
                output += (t.type)
                
    else:
        raise ValueError(f"Input is not list of tiles (type: {type(input)}) or empty")
    
    if output:
        print(f"Level printed:\n")
        print(f"{output}")
    else:
        raise ValueError(f"level printing failed")

############################
#   Level Parsing logic
#
#

def read_level(y: int, line: str, level_return: list[Tile]):
    '''
        reads the current line, convert it to tiles and append them
    '''
    for i in range(0, len(line), 3):     #iterates through the line
        tile_str = line[i:i+3]
        type = tile_str[0]
        conn =tile_str[1] if tile_str[1] != 0 else None
        if tile_str[2] == "1":
            default_state = True
        else: default_state = False
        pos = Pair.new_pair(y, i//3)
        
        tile = Tile.new_tile(type, pos, conn, default_state)
        level_return.append(tile) 

def read_exit(line: str, exits_return: list):
    line = line.replace("(", "")    #cleanse line of "()"
    line = line.replace(")", "")
    line = line.split("-")          #split line into 3:
    cords = line[0]                 #exit position in current level
    nextID = int(line[1])           #next level
    next_cords = line[2]            #spawn pos in the next level
    next_cords = next_cords.split(",")   #turn cords into list of ints by splitting at ","
    cords = cords.split(",")
    exit_pos = Pair.new_pair(cords[1], cords[0]) 
    arrival_pos = Pair.new_pair(next_cords[1], next_cords[0])
    found_exit = (exit_pos, nextID, arrival_pos)
    exits_return.append(found_exit) 

#returns a list of tiles from the input level (3-segment-format)
def tile_from_file(levelID)->list[Tile]:
    if levelID < 20: 
        world = 1
    else: world = 2
    path = LEVEL_PATH+'/levels'+str(world)+'.txt'
    file = open(path)
    content = file.readlines()
    start = "%"+str(levelID)+"%"
    exit_marker = "%"+"exit"+"%"
    end = 3*("%")
    y = 0
    reading_level = False
    reading_exit = False
    level_return: list[Tile] = []
    exits_return: list[(Pair, int, Pair)] = []
    
        
    for c in content:   #iterates through lines "y"
        line = c.strip().replace(" ", "")
        line = line.partition("//")[0]
        if line == "":
            continue
        if start in line:                  #if start marker in current line, start reading level
            reading_level = True
            continue
        if exit_marker in line:                    #if exit_markers marker: start reading exit_markers
            if (reading_level):
                reading_level = False
                reading_exit = True
                continue
        if end in line:                     #if end: end reading 
            if reading_exit:
                reading_level = False
                reading_exit = False
                break
        
        #read the level and convert to tiles
        if reading_level:  
            read_level(y, line, level_return)
            y+=1   
         
        #read the exits    
        elif reading_exit:             
            try:
                read_exit(line, exits_return)
            except IndexError:
                raise IndexError(f"make sure exit format is valid: [(pos)-(ID)-(pos)]")
      
    #yes, i know its a sin to nest ifs, but its easier to read and to debug this way 
    #slightly more inefficient than using a limited second loop, 
        #and also linking if t1 is receiver and t2 activator but idfc  it works ok?
                            
    for x in range(len(level_return)):  #connect the activators and receivers
        t1: Tile = level_return[x]  
        #if tile at x is an activator, and is linked (not conn ID 0)   
        if t1.is_activator() and t1.conn_ID != 0:
            #check through all other tiles
            for y in range(len(level_return)): 
                t2: Tile = level_return[y]
                
            #if second tile is receiver and not first tile
                if t2.is_receiver() and not t2.pos.equal(t1.pos):
                    
                #if they are linked (same conn id)
                    if t1.conn_ID == t2.conn_ID:
                        t1.activ_targets.append(t2.pos.copy())
                        t2.activ_sources.append(t1.pos.copy()) 
                    
                    else: continue
                else: continue
        else: continue
       
    if level_return:
        return level_return, exits_return  
    else:
        raise ValueError(f"the given levelID '{levelID}' does not exist\n{level_return}")  
    
    