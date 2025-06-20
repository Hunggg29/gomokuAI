import random
import uuid

##### Quản lý giao diện #####
SIZE = 540 # kích thước ảnh bàn cờ
PIECE = 32 # kích thước mỗi quân cờ
N = 15
MARGIN = 23
GRID = (SIZE - 2 * MARGIN) / (N-1)

def pixel_conversion(list_points, target):
    # điểm bắt đầu tìm kiếm trong list
    index = int((len(list_points)-1)//2) 

    while True:
        if target < list_points[0]:
            index = 0
            break
        elif target >= list_points[-1]:
            index = len(list_points)-2
            break

        elif list_points[index] > target:
            if list_points[index-1] <= target:
                index -= 1
                break
            else:
                index -= 1

        elif list_points[index] <= target:
            if list_points[index+1] > target:
                break
            else:
                index += 1
    
    return index


# Chuyển đổi pixel pygame sang tọa độ boardMap
def pos_pixel2map(x, y):
    start = int(MARGIN - GRID//2)
    end = int(SIZE - MARGIN + GRID//2)
    list_points = [p for p in range(start, end+1, int(GRID))]

    i = pixel_conversion(list_points, y)
    j = pixel_conversion(list_points, x)
    return (i,j)

# Chuyển đổi boardMap sang pixel pygame
def pos_map2pixel(i, j):
    return (MARGIN + j * GRID - PIECE/2, MARGIN + i * GRID - PIECE/2)


def create_mapping():
    pos_mapping = {}
    for i in range(N):
        for j in range(N):
            spacing = [r for r in range(MARGIN, SIZE-MARGIN+1, int(GRID))]
            pos_mapping[(i,j)] = (spacing[j],spacing[i])
    
    return pos_mapping



#### Pattern scores ####
def create_pattern_dict():
    x = -1
    patternDict = {}
    while (x < 2):
        y = -x
        # long_5
        patternDict[(x, x, x, x, x)] = 1000000 * x
        # live_4
        patternDict[(0, x, x, x, x, 0)] = 100000 * x
        patternDict[(0, x, x, x, 0, x, 0)] = 100000 * x
        patternDict[(0, x, 0, x, x, x, 0)] = 100000 * x
        patternDict[(0, x, x, 0, x, x, 0)] = 100000 * x
        # go_4
        patternDict[(0, x, x, x, x, y)] = 10000 * x
        patternDict[(y, x, x, x, x, 0)] = 10000 * x
        # dead_4
        patternDict[(y, x, x, x, x, y)] = -10 * x
        # live_3
        patternDict[(0, x, x, x, 0)] = 1000 * x
        patternDict[(0, x, 0, x, x, 0)] = 1000 * x
        patternDict[(0, x, x, 0, x, 0)] = 1000 * x
        # sleep_3
        patternDict[(0, 0, x, x, x, y)] = 100 * x
        patternDict[(y, x, x, x, 0, 0)] = 100 * x
        patternDict[(0, x, 0, x, x, y)] = 100 * x
        patternDict[(y, x, x, 0, x, 0)] = 100 * x
        patternDict[(0, x, x, 0, x, y)] = 100 * x
        patternDict[(y, x, 0, x, x, 0)] = 100 * x
        patternDict[(x, 0, 0, x, x)] = 100 * x
        patternDict[(x, x, 0, 0, x)] = 100 * x
        patternDict[(x, 0, x, 0, x)] = 100 * x
        patternDict[(y, 0, x, x, x, 0, y)] = 100 * x
        # dead_3
        patternDict[(y, x, x, x, y)] = -10 * x
        # live_2
        patternDict[(0, 0, x, x, 0)] = 100 * x
        patternDict[(0, x, x, 0, 0)] = 100 * x
        patternDict[(0, x, 0, x, 0)] = 100 * x
        patternDict[(0, x, 0, 0, x, 0)] = 100 * x
        # sleep_2
        patternDict[(0, 0, 0, x, x, y)] = 10 * x
        patternDict[(y, x, x, 0, 0, 0)] = 10 * x
        patternDict[(0, 0, x, 0, x, y)] = 10 * x
        patternDict[(y, x, 0, x, 0, 0)] = 10 * x
        patternDict[(0, x, 0, 0, x, y)] = 10 * x
        patternDict[(y, x, 0, 0, x, 0)] = 10 * x
        patternDict[(x, 0, 0, 0, x)] = 10 * x
        patternDict[(y, 0, x, 0, x, 0, y)] = 10 * x
        patternDict[(y, 0, x, x, 0, 0, y)] = 10 * x
        patternDict[(y, 0, 0, x, x, 0, y)] = 10 * x
        # dead_2
        patternDict[(y, x, x, y)] = -10 * x
        # warning
        patternDict[(x,y,y,y,y,0)] = -1000000 * x
        patternDict[(0,y,y,y,y,x)] = -1000000 * x
        x += 2
    return patternDict



##### Zobrist Hashing #####
def init_zobrist():
    zTable = [[[uuid.uuid4().int  for _ in range(2)] \
                        for j in range(15)] for i in range(15)] #đã đổi thành 32 từ 64
    return zTable

def update_TTable(table, hash, score, depth):
    table[hash] = [score, depth]

def make_move(ai, i, j, turn):
    """
    Thực hiện một nước đi cho AI hoặc người chơi:
    - Cập nhật boardValue
    - Đặt trạng thái
    - Cập nhật currentI, currentJ
    - Cập nhật bound
    - Giảm emptyCells
    - Cập nhật zobrist hash
    """
    ai.boardValue = ai.evaluate(i, j, ai.boardValue, turn, ai.nextBound)
    ai.setState(i, j, turn)
    ai.currentI, ai.currentJ = i, j
    ai.updateBound(i, j, ai.nextBound)
    ai.emptyCells -= 1
    if hasattr(ai, 'zobristTable') and hasattr(ai, 'rollingHash'):
        idx = 0 if turn == 1 else 1
        ai.rollingHash ^= ai.zobristTable[i][j][idx]


def ai_choose_move(ai):
    """
    Để AI chọn nước đi tốt nhất, trả về (i, j).
    """
    import math, time
    start_time = time.time()
    ai.alphaBetaPruning(ai.depth, ai.boardValue, ai.nextBound, -math.inf, math.inf, True)
    end_time = time.time()
    print('AI chose move in', end_time - start_time, 'seconds')
    if ai.isValid(ai.currentI, ai.currentJ):
        move_i, move_j = ai.currentI, ai.currentJ
        ai.updateBound(move_i, move_j, ai.nextBound)
    else:
        print('Error: i and j not valid. Given:', ai.currentI, ai.currentJ)
        ai.updateBound(ai.currentI, ai.currentJ, ai.nextBound)
        bound_sorted = sorted(ai.nextBound.items(), key=lambda el: el[1], reverse=True)
        pos = bound_sorted[0][0]
        move_i, move_j = pos[0], pos[1]
        ai.currentI, ai.currentJ = move_i, move_j
    return move_i, move_j


def ask_restart(game, yes_button, no_button):
    """
    Hiển thị nút hỏi lại chơi, trả về True nếu chọn YES, False nếu chọn NO.
    """
    import pygame
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                if yes_button.rect.collidepoint(mouse_pos):
                    return True
                if no_button.rect.collidepoint(mouse_pos):
                    return False
        pygame.display.update()
