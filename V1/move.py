from pydantic import BaseModel
from typing import Callable
from pair import Pair
from functools import partial

class Move(BaseModel):
    tile: str
    from_x: int
    from_y: int
    speed_x: int
    speed_y: int
    progress: int = 0
    complete: bool = False
    finished: Callable = None
    
def player_update_pos(game, next: Pair):
    game.player.pos = next.copy()
  
def player_state_reset(game):
    game.player.ghost = False
    
def player_next_move(game, target : Pair, current: Pair):
    
    ydistance = target.y-current.y
    xdistance  = target.x-current.x
    better_move: Pair = Pair.new_empty_pair()
    if abs(xdistance) < abs(ydistance):
        print(f"y {ydistance} >= x {xdistance}")
        better_move.x = 0
        if ydistance <0:
            better_move.y = -1
        else: better_move.y = 1
    else:
        better_move.y = 0
        if xdistance <0:
            better_move.x = -1
        else: better_move.x = 1
    
    print(f"moving player from {current} to ", end = "")
    current.add(better_move)
    print(f"{current} (move: {better_move}), target is {target}")
    
    if abs(ydistance+xdistance) > 1:
        f = partial(player_next_move, target = target,current = current)
        move = Move(tile="player",
            from_x = current.x, from_y = current.y,                #from current location
            speed_x = better_move.x,                                                   #speed is spacial difference
            speed_y = better_move.y, 
            finished = f
        ) 
        game.moves.append(move)
    else:
        move = Move(tile="player",
            from_x = current.x, from_y = current.y,                #from current location
            speed_x = better_move.x,                                                   #speed is spacial difference
            speed_y = better_move.y, 
            finished=player_state_reset
        ) 