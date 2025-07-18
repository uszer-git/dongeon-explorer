from pydantic import BaseModel

class Pair(BaseModel):
    y: int
    x: int

    #creates a new pair
    def new_pair(in_y, in_x):
        return Pair(
            x = in_x,
            y = in_y
        )

    #creates a new empty pair for placeholder
    def new_empty_pair():
        return Pair(
            x=0,
            y=0
        )
    
    def copy(self):
        return Pair.new_pair(
            in_y = self.y,
            in_x = self.x, 
        )
    
    #returns if empty pair
    def empty(self)->bool:
        return self.y==0 and self.x ==0
    
    def add(self, other):
        self.x += other.x
        self.y += other.y
    
    #checks if positions (NOT STATE) of two pairs are similar
    def equal(self, other)->bool:
        if self.x == other.x and self.y == other.y:
            return True
        else: return False
