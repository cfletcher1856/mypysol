import os
import sys
from random import shuffle, randint
from pprint import pprint

import pygame
from pygame.locals import *

from refs import refs
from card import Card

# Booleans to track state
refs.status = 'deal'

# So we can use fonts
pygame.font.init()
pygame.display.set_caption("Solitaire")

screen = pygame.display.set_mode((800, 480))
clock = pygame.time.Clock()
fps = clock.get_fps

defaultFont = pygame.font.Font(None, 12)


def createDeck():
    deck = []
    suits = ['h', 'd', 's', 'c']

    for suit in suits:
        for rank in range(1, 14):
            deck.append(Card(rank, suit))

    shuffle(deck)

    refs.deck = deck


def deal_cards():
    createDeck()
    ctr = 1
    while ctr < 8:
        for i in range(1, (9 - ctr)):
            card = refs.deck.pop()
            if i != 1:
                card.is_turned = True
            refs.tableaus[ctr].append(card)

        ctr += 1


def set_layout():
    image = pygame.image.load(os.path.join('images', 'background.png'))
    image = image.convert()
    screen.blit(image, image.get_rect())

    transcard = pygame.image.load(os.path.join('images', 'deck_background.png'))
    screen.blit(transcard, (20, 20))
    screen.blit(transcard, (100, 20))
    screen.blit(transcard, (180, 20))
    screen.blit(transcard, (260, 20))

    # Waste pile
    screen.blit(transcard, (625, 20))

    backofcard = pygame.image.load(os.path.join('images', 'back.png'))
    screen.blit(backofcard, (705, 20))

    if refs.status == 'deal':
        deal_cards()
        refs.status = 'play'

    update_cards()


def update_cards():
    tabelauoffset = 500
    for tabelau in refs.tableaus:
        offset = 0
        for card in reversed(refs.tableaus[tabelau]):
            if card.is_turned:
                cardimg = pygame.image.load(os.path.join('images', 'back.png'))
            else:
                cardimg = pygame.image.load(os.path.join('images', card.img))
            screen.blit(cardimg, (tabelauoffset, 200 + offset))
            offset += 15

        tabelauoffset -= 80

    print len(refs.deck)


def mainGame(framerate=60):
    while 1:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()

        set_layout()

        pygame.display.flip()
        clock.tick(framerate)

if __name__ == "__main__":
    mainGame()


class dealButton(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
