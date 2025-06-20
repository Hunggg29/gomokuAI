import source.utils as utils
from gui.interface import *
from source.AI import *
from gui.button import Button
import pygame

def startGame():
    pygame.init()
    ai = GomokuAI()
    game = GameUI(ai)
    button_black = Button(game.buttonSurf, 200, 290, "BLACK", 22)
    button_white = Button(game.buttonSurf, 340, 290, "WHITE", 22)
    game.drawMenu()
    game.drawButtons(button_black, button_white, game.screen)
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                game.checkColorChoice(button_black, button_white, mouse_pos)
                game.screen.blit(game.board, (0,0))
                pygame.display.update()
                if game.ai.turn == 1:
                    game.ai.firstMove()
                    game.drawPiece('black', game.ai.currentI, game.ai.currentJ)
                    pygame.display.update()
                    game.ai.turn *= -1
                main(game)
                if game.ai.checkResult() != None:
                    last_screen = game.screen.copy()
                    game.screen.blit(last_screen, (0,0))
                    game.drawResult()
                    yes_button = Button(game.buttonSurf, 200, 155, "YES", 18)
                    no_button = Button(game.buttonSurf, 350, 155, "NO", 18)
                    game.drawButtons(yes_button, no_button, game.screen)
                    if utils.ask_restart(game, yes_button, no_button):
                        game.screen.blit(game.board, (0,0))
                        pygame.display.update()
                        game.ai.turn = 0
                        startGame()
                    else:
                        pygame.quit()
        pygame.display.update()
    pygame.quit()

def main(game):
    pygame.init()
    end = False
    result = game.ai.checkResult()
    while not end:
        turn = game.ai.turn
        color = game.colorState[turn]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if turn == 1:
                move_i, move_j = utils.ai_choose_move(game.ai)
                utils.make_move(game.ai, move_i, move_j, turn)
                game.drawPiece(color, move_i, move_j)
                result = game.ai.checkResult()
                game.ai.turn *= -1
            if turn == -1:
                if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                    mouse_pos = pygame.mouse.get_pos()
                    move_i, move_j = utils.pos_pixel2map(mouse_pos[0], mouse_pos[1])
                    if game.ai.isValid(move_i, move_j):
                        utils.make_move(game.ai, move_i, move_j, turn)
                        game.drawPiece(color, move_i, move_j)
                        result = game.ai.checkResult()
                        game.ai.turn *= -1
        if result != None:
            end = True

if __name__ == '__main__':
    startGame()