"""
graphics engine for 2D games

 
"""
import os
import numpy as np
import cv2
import time
from collections import deque
from game import start_game
from pair import Pair

TILE_PATH = os.path.split(__file__)[0] + '/tiles'

# title of the game window
GAME_TITLE = "Dungeon Explorer"

# map keyboard keys to move commands
MOVES = {
    "a": "left",
    "d": "right",
    "w": "up",
    "s": "down",
    " " : "fireball",
}


#
# constants measured in pixels
#
SCREEN_SIZE_X, SCREEN_SIZE_Y = 832, 640
TILE_SIZE = 64



def read_image(filename: str) -> np.ndarray:
    """
    Reads an image from the given filename and doubles its size.
    If the image file does not exist, an error is created.
    """
    img = cv2.imread(filename)  # sometimes returns None
    if img is None:
        raise IOError(f"Image not found: '{filename}'")
    if TILE_SIZE != 32:
#COMMENT OUT THIS LINE IF USING NOT 64 PIXEL TILES
        img = np.kron(img, np.ones((2, 2, 1), dtype=img.dtype))  # double image size
#--------------------------------------
    return img


def read_images():
    return {
        filename[:-4]: read_image(os.path.join(TILE_PATH, filename))
        for filename in os.listdir(TILE_PATH)
        if filename.endswith(".png")
    }


def draw_tile(frame, x, y, image, xbase=0, ybase=0):
    # calculate screen position in pixels
    xpos = xbase + x * TILE_SIZE
    ypos = ybase + y * TILE_SIZE
    if xpos>SCREEN_SIZE_X-TILE_SIZE or ypos>SCREEN_SIZE_X-TILE_SIZE:
        return
    # copy the image to the screen
    frame[ypos : ypos + TILE_SIZE, xpos : xpos + TILE_SIZE] = image


def draw_move(frame, move, images):
    draw_tile(frame, x=move.from_x, y=move.from_y, image=images[move.tile], xbase=move.progress * move.speed_x, ybase=move.progress * move.speed_y)
    move.progress += 1


def clean_moves(game, moves):
    result = []
    for m in moves:
        if m.progress * max(abs(m.speed_x), abs(m.speed_y)) < TILE_SIZE:
            result.append(m)
        else:
            m.complete = True
            if m.finished is not None:
                m.finished(game)
    return result

def is_player_moving(moves):
    return any([m for m in moves if m.tile == "player"])


def draw(frame, game, images, moves):
    # initialize screen
    
        # draw dungeon tiles
    for t in game.level.lvl:
        draw_tile(frame, x=t.pos.x, y=t.pos.y, image = images[t.sprite])

    #draw the HUD
    draw_HUD(game, images, frame)
    
    # draw player
    while game.moves:
        moves.append(game.moves.pop())
    if not is_player_moving(moves):
        draw_tile(frame=frame, x=game.player.pos.x, y=game.player.pos.y, image=images["player"])
    
    # draw everything that moves (loop FIX!)
    for m in moves:
        draw_move(frame=frame, move=m, images=images)
        
        
def draw_HUD(game, images, frame):
    #draw gold
    cv2.putText(frame,
            str(str(game.player.coins)+" Gold"),
            org=(750, 52),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.5,
            color=(10, 140, 200),
            thickness=2,
            )
    draw_tile(frame, xbase=650, ybase=20, x=0, y=0, image = images["coin"] )
    #draw hp
    for i in range(game.player.hp):
        draw_tile(frame=frame, xbase=640, ybase = 400, x=i, y = 0, image = images["heart_black"])
    #draw room number because easier
    cv2.putText(frame, ("room"+str(game.level.ID)),
                org = (750, 620),fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.3, color=(255, 255, 255), thickness = 1)
    #draw inventory
    for i, item in enumerate(game.player.inv):
        y = i // 2  # floor division: rounded down
        x = i % 2   # modulo: remainder of an integer division
        draw_tile(frame, xbase=660, ybase=96, x=x, y=y, image=images[item.sprite])
     
    #draw game lines
    if game.show_lines: 
        for j, i in enumerate(game.lines):
            i["s"] -=1
            if i["s"] <= 0:
                game.lines.remove(i)
                continue
            
            pos1 = (int((i["p1"].x*TILE_SIZE)+TILE_SIZE/2), int((i["p1"].y*TILE_SIZE)+TILE_SIZE/2))
            pos2: list[Pair] = i["p2"]
            col = i["c"]
            for k in range(len(pos2)):
                p2 = (int(pos2[k].x*TILE_SIZE+TILE_SIZE/2), int(pos2[k].y*TILE_SIZE+5))
                cv2.line(frame, pt1=pos1, pt2=p2, 
                        color=col, thickness=2)
        
    #put game text
    for j, i in enumerate(game.text):
            text = i["t"]
            i["s"] -= 1
            if i["s"] <= 0:
                game.text.remove(i)
                
            orgx = game.player.pos.x * TILE_SIZE
            orgy = (game.player.pos.y * TILE_SIZE)-(j)*20
            if orgx+len(text)*10 > SCREEN_SIZE_X:
                orgx = SCREEN_SIZE_X - len(text) * 10
            cv2.putText(frame, text, org = (orgx, orgy), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.6, color= i["c"], thickness=2)

def handle_keyboard(game):
    """keys are mapped to move commands"""
    key = chr(cv2.waitKey(1) & 0xFF)
    if key == "q":
        cheater(game)
        game.status = "exited"
    if key == "g":
        cheater(game)
        game.player.ghost = not game.player.ghost
        print(f"player is ghost: {game.player.ghost}")
        return None
    if key == "h":
        cheater(game)
        if game.player.hp > game.player.max_hp:
            game.player.hp = game.player.max_hp
        else: game.player.hp = 1000
        return None
    if key == "m":
        cheater(game)
        game.player.coins = 100
        return None
    if key == "l":
        game.show_lines = not game.show_lines
        return None
    
    return MOVES.get(key)

def cheater(game):
    game.text.append({"t": "It seems you cheated. if u arent me, fuck u", "s": 300, "c": (255, 255, 255)})

def main():
    images = read_images()
    game = start_game(10)
    queued_move = None
    moves = []
    fps = []
    plot = deque(maxlen = 200)
    plot_y = 640
    frame_count = 0
    next_display_time = time.time() + 1 
    avrg_fps = 0


    while game.status == "running":
        frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)
        #get start time of current game loop
        start_time = time.time() 
         
        #game logic
        draw(frame, game, images, moves)
        moves = clean_moves(game, moves)
        queued_move = handle_keyboard(game)
        if not is_player_moving(moves):
            game.update(queued_move)
            
        #fps logic
        if True:
            elapsed_time = time.time()-start_time
            fps.append(1/elapsed_time)
            frame_count+=1
            if time.time() > next_display_time:
                avrg_fps = sum(fps)
                avrg_fps =  avrg_fps/len(fps)
                next_display_time = time.time()+1
                fps = []
                fps.append(avrg_fps)
            if avrg_fps:
                cv2.putText(frame, 
                            "FPS:"+str(f'{avrg_fps:.2f}'),
                            org=(640, 630),
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=0.5,
                            color=(0, 0, 255),
                            thickness=1,
                            )
                plot.append(avrg_fps)
                if len(plot)>2:
                    for i in range(len(plot)-1):
                        x1 = 640+i*1
                        y1 = int(plot_y-plot[i]/5)
                        x2 = 640+(i+1)*1 
                        y2 = int(plot_y - plot[i+1]/5)
                        cv2.line(frame,(x1, y1),(x2, y2), (0, 0, 255), 1)
        # display complete image
        cv2.imshow(GAME_TITLE, frame)

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
