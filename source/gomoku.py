import math
import time
import pygame
from source.AI import *
from gui.interface import *
import source.utils as utils 

pygame.init()

def ai_move(ai):
    # Sử dụng hàm tiện ích mới
    move_i, move_j = utils.ai_choose_move(ai)
    return move_i, move_j

def check_human_move(ai, mouse_pos):
    move_i, move_j = utils.pos_pixel2map(mouse_pos[0], mouse_pos[1])
    if ai.isValid(move_i, move_j):
        utils.make_move(ai, move_i, move_j, -1)
        return move_i, move_j

def check_results(ui, result):
    if result == 0:
        print("it's a tie!")
        ui.drawResult(tie=True)
    else:
        ui.drawResult()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN\
                    and pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                ui.restartChoice(mouse_pos)
    

