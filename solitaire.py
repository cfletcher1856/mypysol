import os
import sys
from random import shuffle

import pygame
from pygame.locals import *

from card import Card

# So we can use fonts
pygame.font.init()

screen = pygame.display.set_mode((800, 480))
screen.fill((0, 0, 0))

clock = pygame.time.Clock()
defaultFont = pygame.font.Font(None, 12)


def createDeck():
    deck = []
    suits = ['h', 'd', 's', 'c']

    for suit in suits:
        for rank in range(1, 14):
            deck.append(Card(rank, suit))

    shuffle(deck)

    return deck


def mainGame():
    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()

        hello = pygame.font.Font.render(defaultFont, "Hello", True, (255, 255, 255), (0, 0, 0))
        screen.blit(hello, (125, 10))

        pygame.display.flip()

if __name__ == "__main__":
    mainGame()
