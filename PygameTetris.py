#! /usr/bin/env python
# -*- coding: utf-8 -*-
# A Pygame Implementation of Tetris
# Author: Billy Donegan (billydonegan76)
# Date 24/02/2021
# To Do:
# --------- GAME  5 Bugs :( ---------------------------
# FIXED - Handle issue with rotation into Wall which creates >10 items per line and then everything breaks
# FIXED - Putting a Tetromino under a line makes it stop which is wrong; it should continue to drop
# FIXED - Rare glitch with rotating at very bottom (Fixed by key handle event)
# FIXED - Ceiling Bug where not checking overlap for created Tetromino. THIS IMPACTS BOTH GAMEs
# FIXED - Fast Down is a problem too (Fixed by key handle event)
# TO FIX - Tetromino clearing is not working either e.g 10,10,10,10,9,7,3 -> 9,10 -> 9 which is not right - Line 412
# Optional - Add a ghost Tetromino (Ignoring for now)
# Optional - Screen size is not changing based on screen_height (HOME SCREEN WORKS NOW - Ignoring Re-sizing for now)
# Optional- Rotation at right edge of screen fails for resizing (e.g. 400) (Ignoring Re-sizing for now)

# -------- Machine Learning -------------------------
# Want a neural network (DQN) with parameters that takes in the current state and returns a value 0 - 4
# Initiation of parameters can be random initially but needs to be read from a File
# DONE - Moving based on that number is implemented (we have a brain but its an RNG...)
# To Do - Populate based on a DQN not a Random number. Params Don't matter right not so will be crap
# 1. Implement a DQN
# 2. Use DQN to drive moves
# 3. Train DQN
# 4. Store, load, saved trained states and game

# -------- Machine Learning Training ----------------
# Key Expectation for training is that this must ultimately be able to run without screen
# (but can show the game progressing)
# Can be considered a function that takes a seed, sequence of inputs and returns a score.
# Will aim to wrap in a Reinforcement Learning Process for AI Tetris Player (but one step at a time...)
# Incrementing of parameters is part of training and needs to be output as a File

# ------- Porting To Android (IGNORING FOR NOW)-----------------
# Port to Kivy
# Last Step: Turn into a callable function with graphics switchable on or off
# DONE - Accept inputs from code not from keys
import time
import tensorflow as tf
import sys
import math
import random
import pygame
from pygame.locals import *
from pynput.keyboard import Key, Controller

keyboard = Controller()

# Global Variables - Should Not Change
screen_height = 800
number_of_columns = 10
number_of_rows = 40
screen_width = int(screen_height / 4)
tetromino_start_x = int(screen_width / 2) - int(screen_width / number_of_columns)
tetromino_start_y = int(screen_height / number_of_rows)
print(int(screen_width / number_of_columns))

# Timers
fpsclock = pygame.time.Clock()
s = time.time()


# Create Classes:
class Brain:
    def __init__(self, brainoutputoptions):
        self.Output_options = brainoutputoptions
        self.key = []

    def makeamove(self):
        keyboard.release(Key.space)
        keyboard.release(Key.right)
        keyboard.release(Key.left)
        keyboard.release(Key.down)
        keyboard.release('z')
        self.key = random.randint(0, self.Output_options)  # This single line is what will be replaced by the DQN
        if self.key == 0:
            keyboard.press(Key.space)
        elif self.key == 1:
            keyboard.press(Key.right)
        elif self.key == 2:
            keyboard.press(Key.left)
        elif self.key == 3:
            keyboard.press(Key.down)
        elif self.key == 4:
            keyboard.press('z')


class GenericBrick(pygame.sprite.Sprite):
    def __init__(self, x, y, r, g, b, org):
        super(GenericBrick, self).__init__()
        self.surf = pygame.Surface((screen_width / number_of_columns, screen_width / number_of_columns))
        self.surf.fill((r, g, b))
        self.rect = self.surf.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.Xcoord = x
        self.Ycoord = y
        self.red = r
        self.green = g
        self.blue = b
        self.origin = org
        self.bottom = int(self.Ycoord + screen_width / number_of_columns)


class Tetromino:
    def __init__(self, tetrominotype, ghostflag):
        super(Tetromino, self).__init__()
        self.bricks = []
        self.leftEdge = False
        self.rightEdge = False
        self.wallOverlap = False
        self.ghost = ghostflag
        self.type = tetrominotype
        self.rotationAngle = 0
        if tetrominotype == 0:  # 0 . No Rotation or Variants so no function required
            self.bricks.append(GenericBrick(tetromino_start_x, tetromino_start_y, 255, 255, 0, True))
            self.bricks.append(
                GenericBrick(tetromino_start_x + int(screen_width / number_of_columns), tetromino_start_y, 255, 255, 0,
                             False))
            self.bricks.append(
                GenericBrick(tetromino_start_x, tetromino_start_y + int(screen_height / number_of_rows), 255, 255, 0,
                             False))
            self.bricks.append(GenericBrick(tetromino_start_x + int(screen_width / number_of_columns),
                                            tetromino_start_y + int(screen_height / number_of_rows), 255, 255, 0,
                                            False))
        else:
            self.rotationAngle = 270  # Just trigger a rotation to 0 to draw a new Tetromino in place.
            self.rotate()

    def rotate(self):  # Calling this with 270 will draw a new piece
        x = 0
        y = 0
        self.rotationAngle = (self.rotationAngle + 90) % 360
        if not self.bricks:
            x = tetromino_start_x
            y = tetromino_start_y  # If this is a new Tetromino set the Origin Block
        for brick in self.bricks:  # This moves the origin block for some specific scenarios of J,L and I
            if brick.origin:
                if self.type == 1 and (self.rotationAngle == 90 or self.rotationAngle == 270):
                    x = brick.Xcoord + int(screen_width / number_of_columns)
                    y = brick.Ycoord
                if self.type == 1 and (self.rotationAngle == 0 or self.rotationAngle == 180):
                    x = brick.Xcoord - int(screen_width / number_of_columns)
                    y = brick.Ycoord
                else:
                    x = brick.Xcoord
                    y = brick.Ycoord

            # Need to handle wall events now too
        if self.type == 1:  # I
            if self.rotationAngle == 0 or self.rotationAngle == 180:
                if x - int(screen_width / number_of_columns) >= 0 and x + int(screen_width / number_of_columns) <= 160:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x, y, 0, 255, 255, True))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 0, 255, 255, True))
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns), y, 0, 255, 255, False))
                    self.bricks.append(
                        GenericBrick(x + 2 * int(screen_width / number_of_columns), y, 0, 255, 255, False))
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 90 or self.rotationAngle == 270:
                if y < screen_height - 2 * int(screen_width / number_of_columns):
                    self.bricks = []
                    self.bricks.append(GenericBrick(x, y, 0, 255, 255, True))
                    self.bricks.append(GenericBrick(x, y + int(screen_height / number_of_rows), 0, 255, 255, False))
                    self.bricks.append(GenericBrick(x, y - int(screen_height / number_of_rows), 0, 255, 255, False))
                    self.bricks.append(
                        GenericBrick(x, y + 2 * int(screen_height / number_of_rows), 0, 255, 255, False))
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
        elif self.type == 2:  # Z
            if self.rotationAngle == 0 or self.rotationAngle == 180:
                if x - int(screen_width / number_of_columns) >= 0:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns), y, 255, 0, 0, False))
                    self.bricks.append(GenericBrick(x, y, 255, 0, 0, True))
                    self.bricks.append(GenericBrick(x, y + int(screen_height / number_of_rows), 255, 0, 0, False))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                    y + int(screen_height / number_of_rows), 255, 0, 0, False))
            elif self.rotationAngle == 90 or self.rotationAngle == 270:
                self.bricks = []
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 255, 0, 0, False))
                self.bricks.append(GenericBrick(x, y, 255, 0, 0, True))
                self.bricks.append(GenericBrick(x, y + int(screen_height / number_of_rows), 255, 0, 0, False))
                self.bricks.append(GenericBrick(x + 1 * int(screen_width / number_of_columns),
                                                y - int(screen_height / number_of_rows), 255, 0, 0, False))
        elif self.type == 3:  # S
            if self.rotationAngle == 0 or self.rotationAngle == 180:
                if x - int(screen_width / number_of_columns) >= 0:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 0, 255, 0, False))
                    self.bricks.append(GenericBrick(x, y, 0, 255, 0, True))
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                    y + int(screen_height / number_of_rows), 0, 255, 0, False))
                    self.bricks.append(GenericBrick(x, y + int(screen_height / number_of_rows), 0, 255, 0, False))
            elif self.rotationAngle == 90 or self.rotationAngle == 270:
                self.bricks = []
                self.bricks.append(GenericBrick(x, y, 0, 255, 0, True))
                self.bricks.append(GenericBrick(x + 1 * int(screen_width / number_of_columns), y, 0, 255, 0, False))
                self.bricks.append(GenericBrick(x + 1 * int(screen_width / number_of_columns),
                                                y + int(screen_height / number_of_rows), 0, 255, 0, False))
                self.bricks.append(GenericBrick(x, y - 1 * int(screen_height / number_of_rows), 0, 255, 0, False))
        elif self.type == 4:  # T
            if self.rotationAngle == 0:
                if x < 180:
                    self.bricks = []
                    self.bricks.append(
                        GenericBrick(x, y - int(screen_height / number_of_rows), 128, 0, 128, False))  # 1
                    self.bricks.append(GenericBrick(x, y, 128, 0, 128, True))  # 0
                    self.bricks.append(
                        GenericBrick(x + int(screen_width / number_of_columns), y, 128, 0, 128, False))  # 3
                    self.bricks.append(
                        GenericBrick(x - int(screen_width / number_of_columns), y, 128, 0, 128, False))  # 2
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 90:
                self.bricks = []
                self.bricks.append(GenericBrick(x, y - int(screen_height / number_of_rows), 128, 0, 128, False))  # 1
                self.bricks.append(GenericBrick(x, y, 128, 0, 128, True))  # 0
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 128, 0, 128, False))  # 3
                self.bricks.append(GenericBrick(x, y + int(screen_height / number_of_rows), 128, 0, 128, False))  # 4
            elif self.rotationAngle == 180:
                if x > 0:
                    self.bricks = []
                    self.bricks.append(
                        GenericBrick(x - int(screen_width / number_of_columns), y, 128, 0, 128, False))  # 2
                    self.bricks.append(GenericBrick(x, y, 128, 0, 128, True))  # 0
                    self.bricks.append(
                        GenericBrick(x + int(screen_width / number_of_columns), y, 128, 0, 128, False))  # 3
                    self.bricks.append(
                        GenericBrick(x, y + int(screen_height / number_of_rows), 128, 0, 128, False))  # 4
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 270:
                self.bricks = []
                self.bricks.append(GenericBrick(x, y - int(screen_height / number_of_rows), 128, 0, 128, False))  # 1
                self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns), y, 128, 0, 128, False))  # 2
                self.bricks.append(GenericBrick(x, y, 128, 0, 128, True))  # 0
                self.bricks.append(GenericBrick(x, y + int(screen_height / number_of_rows), 128, 0, 128, False))  # 4
        elif self.type == 5:  # L
            if self.rotationAngle == 0:
                if x < 180:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 255, 165, 0, False))
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                    self.bricks.append(GenericBrick(x, y + 1 * int(screen_height / number_of_rows), 255, 165, 0, True))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 90:
                self.bricks = []
                self.bricks.append(GenericBrick(x, y, 255, 165, 0, False))
                self.bricks.append(GenericBrick(x, y - 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                self.bricks.append(GenericBrick(x, y - 2 * int(screen_height / number_of_rows), 255, 165, 0, True))
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 255, 165, 0, False))
            elif self.rotationAngle == 180:
                if x > 0:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                    y + 2 * int(screen_height / number_of_rows), 255, 165, 0, False))
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 255, 165, 0, True))
                    self.bricks.append(
                        GenericBrick(x, y + 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 270:
                self.bricks = []
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                y - 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns), y, 255, 165, 0, True))
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                y + 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
                self.bricks.append(GenericBrick(x, y - 1 * int(screen_height / number_of_rows), 255, 165, 0, False))
        elif self.type == 6:  # J
            if self.rotationAngle == 0:
                if x < 180:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns), y, 0, 0, 255, False))
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 0, 0, 255, False))
                    self.bricks.append(GenericBrick(x, y + 1 * int(screen_height / number_of_rows), 0, 0, 255, True))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 0, 0, 255, False))
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 90:
                self.bricks = []
                self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                y - 2 * int(screen_height / number_of_rows), 0, 0, 255, False))
                self.bricks.append(GenericBrick(x, y - 2 * int(screen_height / number_of_rows), 0, 0, 255, True))
                self.bricks.append(GenericBrick(x, y - int(screen_height / number_of_rows), 0, 0, 255, False))
                self.bricks.append(GenericBrick(x, y, 0, 0, 255, False))
            elif self.rotationAngle == 180:
                if x > 0:
                    self.bricks = []
                    self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 0, 0, 255, False))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                    y + 2 * int(screen_height / number_of_rows), 0, 0, 255, False))
                    self.bricks.append(GenericBrick(x, y + 1 * int(screen_height / number_of_rows), 0, 0, 255, True))
                    self.bricks.append(GenericBrick(x + int(screen_width / number_of_columns),
                                                    y + 1 * int(screen_height / number_of_rows), 0, 0, 255, False))
                else:
                    self.rotationAngle = (self.rotationAngle - 90) % 360
            elif self.rotationAngle == 270:
                self.bricks = []
                self.bricks.append(GenericBrick(x, y - 1 * int(screen_height / number_of_rows), 0, 0, 255, False))
                self.bricks.append(GenericBrick(x, y, 0, 0, 255, True))
                self.bricks.append(GenericBrick(x, y + 1 * int(screen_height / number_of_rows), 0, 0, 255, False))
                self.bricks.append(GenericBrick(x - int(screen_width / number_of_columns),
                                                y + 1 * int(screen_height / number_of_rows), 0, 0, 255, False))

    def update(self, pressed_keys, wall, score, number_of_rows_with_no_downkey):
        self.leftEdge = False
        self.rightEdge = False

        # Left and Right need something to stop them moving when they hit the bottom. That will solve most of the issue
        if pressed_keys[K_LEFT]:
            for brick in self.bricks:
                if brick.rect.left <= 0:
                    self.leftEdge = True
                for wallBrick in wall.bricks:
                    if brick.Xcoord - int(screen_width / number_of_columns) == wallBrick.Xcoord:
                        if brick.Ycoord == wallBrick.Ycoord:
                            self.leftEdge = True
            if self.leftEdge is False and self.wallOverlap is False:
                for brick in self.bricks:
                    brick.Xcoord = brick.Xcoord - int(screen_width / number_of_columns)
                    brick.rect.x = brick.Xcoord

        if pressed_keys[K_RIGHT]:
            for brick in self.bricks:
                if brick.rect.right >= screen_width:
                    self.rightEdge = True
                for wallBrick in wall.bricks:
                    if brick.Xcoord + int(screen_width / number_of_columns) == wallBrick.Xcoord:
                        if brick.Ycoord == wallBrick.Ycoord:
                            self.rightEdge = True
            if self.rightEdge is False and self.wallOverlap is False:
                for brick in self.bricks:
                    brick.Xcoord = brick.Xcoord + int(screen_width / number_of_columns)
                    brick.rect.x = brick.Xcoord

        if pressed_keys[K_DOWN]:
            for brick in self.bricks:
                if brick.Ycoord > number_of_rows_with_no_downkey * int(screen_height / number_of_rows):
                    while self.wallOverlap is False:
                        self.drop_tetromino(wall)
                        score += 1

        if pressed_keys[K_SPACE]:
            self.rotate()

        if pressed_keys[K_z]:
            self.drop_tetromino(wall)
            score += 1

        return score

    def drop_tetromino(self, wall):
        for brick in self.bricks:
            if brick.bottom >= screen_height:
                self.wallOverlap = True
            for wallBrick in wall.bricks:
                if brick.Xcoord == wallBrick.Xcoord:
                    if brick.Ycoord + int(screen_height / number_of_rows) == wallBrick.Ycoord:
                        self.wallOverlap = True
        if self.wallOverlap is True:
            for brick in self.bricks:
                new_brick = GenericBrick(brick.Xcoord, brick.Ycoord, brick.red, brick.green, brick.blue, False)
                wall.bricks.append(new_brick)
        elif self.wallOverlap is False:
            for brick in self.bricks:
                brick.Ycoord = brick.Ycoord + int(screen_height / number_of_rows)
                brick.rect.y = brick.Ycoord
                brick.bottom = int(brick.Ycoord + screen_width / number_of_columns)


class WallClass:
    def __init__(self):
        self.bricks = []
        self.bricksperLine = []
        self.completeRows = []
        self.tooHigh = False
        super(WallClass, self).__init__()

    def clearlines(self, level, score):

        # Initialise
        self.bricksperLine = [0] * number_of_rows
        self.completeRows = []

        # Build Wall Brick Count Array
        for i in range(0, number_of_rows):
            for brick in self.bricks:
                if brick.Ycoord == screen_height - (i + 1) * int(screen_width / number_of_columns):
                    self.bricksperLine[i] = self.bricksperLine[i] + 1

        print(self.bricksperLine)  # THIS WILL TELL YOU WHEN THE ISSUE IS RESOLVED. ONLY DOWN TO ROTATION NOW

        # Check for GameOver. This is still needed if the block goes over the line
        if self.bricksperLine[number_of_rows - 1] > 0:
            return -1

        # Search for and remove Complete Rows --- This needs work
        for i in range(0, number_of_rows):
            if self.bricksperLine[i] >= number_of_columns:
                self.bricks = [brick for brick in self.bricks if
                               brick.Ycoord != (screen_height - (i + 1) * int(screen_width / number_of_columns))]
                self.completeRows.append(i)

        if len(self.completeRows) == 1:
            score += 40 * (level + 1)
        elif len(self.completeRows) == 2:
            score += 100 * (level + 1)
        elif len(self.completeRows) == 3:
            score += 300 * (level + 1)
        elif len(self.completeRows) == 4:
            score += 1200 * (level + 1)

        # Drop Down Lines
        while len(self.completeRows) > 0:
            for i in range(self.completeRows[-1] + 1, number_of_rows):
                for brick in self.bricks:
                    if brick.Ycoord < screen_height - i * int(screen_width / number_of_columns):
                        brick.Ycoord = brick.Ycoord + int(screen_height / number_of_rows)
                        brick.rect.y = brick.Ycoord
                        brick.bottom = int(brick.Ycoord + screen_width / number_of_columns)
            self.completeRows.pop(-1)
        return score


class TetrisGame(pygame.sprite.Sprite):
    def __init__(self):
        self.drop_Tetromino_speed = 500
        self.drop_Tetromino_speed_rate = 10
        self.level_speed_rate = 45
        self.FPS = 10
        self.screen_Caption = "Tetris"
        self.number_of_rows_with_no_downkey = 3
        self.seed = 1234  # Can be randomised if needed
        pygame.init()
        self.screen_dim = (screen_width, screen_height)  # Screen Size
        self.screen = pygame.display.set_mode(self.screen_dim)
        self.screen_bg_colour = (0, 0, 0)
        self.screen.fill(self.screen_bg_colour)
        self.drop_Tetromino = pygame.USEREVENT + 1
        pygame.time.set_timer(self.drop_Tetromino, self.drop_Tetromino_speed)
        self.tetromino_Count = 0
        self.score = 0
        self.level = 0
        self.paused = False
        self.activeGame = False
        self.player = "Human"  # "Human"
        self.tetromino_Index = [0, 1, 2, 3, 4, 5, 6]
        random.Random(self.seed).shuffle(self.tetromino_Index)
        # Instantiate our Tetromino - A wall, a tetromino
        self.tetromino = Tetromino(self.tetromino_Index[0], False)
        self.ghost_tetromino = Tetromino(self.tetromino_Index[0], False)
        self.rotation_test_tetromino = Tetromino(self.tetromino_Index[0], False)
        self.tetris_Wall = WallClass()  # For drawing target location of Tetromino
        self.Brain = Brain(4)
        super(TetrisGame, self).__init__()

    def handleevents(self):
        # Handle Quit and drop timer
        for event in pygame.event.get():
            if event.type == QUIT:  # This may need to be adjusted for automated re-starts. same as game over trigger
                sys.exit()
            elif event.type == self.drop_Tetromino and self.paused is False:
                self.tetromino.drop_tetromino(self.tetris_Wall)

        if self.player == "Machine":
            Brain.makeamove(self.Brain)

        # Handle inputs for the game and pass Tetromino moves to the Tetromino object
        pressed_keys = pygame.key.get_pressed()
        pygame.event.set_blocked(pygame.KEYDOWN)
        if pressed_keys[K_n]:
            print("New Game!")
            keyboard.release(Key.space)
            keyboard.release(Key.right)
            keyboard.release(Key.left)
            keyboard.release(Key.down)
            keyboard.release('z')
            # Instantiate our Tetromino for next game
            self.tetromino_Index = [0, 1, 2, 3, 4, 5, 6]
            random.Random(self.seed).shuffle(self.tetromino_Index)
            # random.shuffle(tetromino_Index)
            self.tetromino = Tetromino(self.tetromino_Index[0], False)
            self.tetris_Wall = WallClass()
            self.score = 0
            self.level = 0
            self.tetromino_Count = 0
            self.activeGame = True
            self.player = "Human"

        if pressed_keys[K_m]:
            print("New Machine Game!")
            # Instantiate our Tetromino for next game
            self.tetromino_Index = [0, 1, 2, 3, 4, 5, 6]
            random.Random(self.seed).shuffle(self.tetromino_Index)
            # random.shuffle(tetromino_Index)
            self.tetromino = Tetromino(self.tetromino_Index[0], False)
            self.tetris_Wall = WallClass()
            self.score = 0
            self.level = 0
            self.tetromino_Count = 0
            self.activeGame = True
            self.player = "Machine"

        if pressed_keys[K_p]:
            self.paused = not self.paused

        if pressed_keys[K_q]:
            self.activeGame = False

        if pressed_keys[K_e]:
            exit()

        pygame.event.set_allowed(pygame.KEYDOWN)

    def updateactivegame(self, pressed_keys):
        self.score = self.tetromino.update(pressed_keys, self.tetris_Wall, self.score,
                                           self.number_of_rows_with_no_downkey)
        score_candidate = self.tetris_Wall.clearlines(self.level, self.score)
        if score_candidate == -1:
            self.activeGame = False
        else:
            self.score = score_candidate

        if self.tetromino.wallOverlap is True:
            self.tetromino_Count = self.tetromino_Count + 1
            tetromino_type = self.tetromino_Index[self.tetromino_Count % 7]
            print("New Tetromino")
            self.tetromino = Tetromino(tetromino_type, False)
            #self.ghost_tetromino = Tetromino(tetromino_type, True)
            #self.rotation_test_tetromino = Tetromino(tetromino_type, True)
            if (self.tetromino_Count % 7) == 6:
                random.Random().shuffle(self.tetromino_Index)
            # THIS MIGHT BE PART OF THE SOLUTION
            for brick in self.tetromino.bricks:
                for wallBrick in self.tetris_Wall.bricks:
                    if brick.rect.x == wallBrick.rect.x:
                        if brick.rect.y == wallBrick.rect.y :
                            self.tetromino.wallOverlap = True
                            print("Overlap so end game")
                            self.activeGame = False

        # Redraw, so clear screen, fill background, redraw wall and redraw tetromino
        if self.activeGame == True:
            self.screen.fill(self.screen_bg_colour)

        # Display Score
        msg = "Score: " + str(self.score)
        msg_color = (255, 255, 255)
        f = pygame.font.SysFont(None, 24)
        msg_image = f.render(msg, True, msg_color, None)
        scoresurf = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        scorerect = scoresurf.get_rect()
        scorerect.x = 100
        scorerect.y = 0
        self.screen.blit(msg_image, scorerect)

        # Display Level
        if math.floor(int(time.time() - s) / int(self.level_speed_rate)) > self.level:
            self.level += 1
            self.drop_Tetromino_speed -= self.drop_Tetromino_speed_rate
            pygame.time.set_timer(self.drop_Tetromino, max(self.drop_Tetromino_speed, 1))

        level_msg = "Level: " + str(self.level)
        level_msg_color = (255, 255, 0)
        g = pygame.font.SysFont(None, 24)
        level_msg_image = g.render(level_msg, True, level_msg_color, None)
        levelsurf = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        levelrect = levelsurf.get_rect()
        levelrect.x = 0
        levelrect.y = 0
        self.screen.blit(level_msg_image, levelrect)

        # Draw Bricks and Draw Wall
        if self.activeGame == True:
            for brick in self.tetromino.bricks:
                brick.rect.x = brick.Xcoord
                brick.rect.y = brick.Ycoord
                self.screen.blit(brick.surf, brick.rect)
            for brick in self.tetris_Wall.bricks:
                self.screen.blit(brick.surf, brick.rect)

    def updatepausedgame(self):
        oldscore = self.score
        oldlevel = self.level
        oldcount = self.tetromino_Count
        self.screen.fill(self.screen_bg_colour)
        start_msg1 = "TETRIS: (N)ew/(M)achine"
        start_msg1_color = (255, 0, 0)
        start_msg2 = "Tetrominos: " + str(oldcount)
        start_msg2_color = (255, 255, 255)
        start_msg3 = "Level: " + str(oldlevel)
        start_msg3_color = (255, 255, 255)
        start_msg4 = "Score: " + str(oldscore)
        start_msg4_color = (255, 255, 255)
        g = pygame.font.SysFont(None, 22)  # - math.ceil(800/screen_height))
        g2 = pygame.font.SysFont(None, 16)  # - math.ceil(800/screen_height))
        start_msg1_image = g.render(start_msg1, True, start_msg1_color, None)
        start_msg2_image = g2.render(start_msg2, True, start_msg2_color, None)
        start_msg3_image = g2.render(start_msg3, True, start_msg3_color, None)
        start_msg4_image = g2.render(start_msg4, True, start_msg4_color, None)
        startsurf1 = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        startsurf2 = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        startsurf3 = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        startsurf4 = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        startrect1 = startsurf1.get_rect()
        startrect2 = startsurf2.get_rect()
        startrect3 = startsurf3.get_rect()
        startrect4 = startsurf4.get_rect()

        startrect1.x = 10
        startrect1.y = 400
        self.screen.blit(start_msg1_image, startrect1)
        startrect2.x = 30
        startrect2.y = 440
        self.screen.blit(start_msg2_image, startrect2)
        startrect3.x = 30
        startrect3.y = 480
        self.screen.blit(start_msg3_image, startrect3)
        startrect4.x = 30
        startrect4.y = 520
        self.screen.blit(start_msg4_image, startrect4)


# Main Function
def play_tetris():
    tetrisgame = TetrisGame()

    # Main Program Loop
    while True:
        tetrisgame.handleevents()

        if tetrisgame.paused is False and tetrisgame.activeGame is True:
            tetrisgame.updateactivegame(pygame.key.get_pressed())
        elif not tetrisgame.activeGame:
            tetrisgame.updatepausedgame()

        # Flip to newly drawn screen and increment clock
        pygame.display.flip()
        fpsclock.tick(tetrisgame.FPS)


# Start Game
play_tetris()
print(time.time() - s)