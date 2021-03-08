#! /usr/bin/env python
# -*- coding: utf-8 -*-
# A Pygame Reinforcement Learning Implementation of Tetris
# Author: Billy Donegan (billydonegan76)
# Date 03/03/2021
# --------- 1. GAME ---------------------------
# TO DO: NEW BUG - Rotate is not working. Not checking for wall block before rotation only checking edge
# TO DO: NEW BUG - Still some issues at top level with overlaps (Might be resolved by above or else a try/catch)
# TO DO: Refactor? to seperate graphics from the game.
# -------- 3. Machine Learning Training ----------------
# 4b. Save down logs (not just model) after game finishes
# 4c. The  big step is to update model after each game. Need to think about hyperparameter tuning
# -------- 4. WebApp, Deployment and Cloud Storage/Compute ----------------
# Looks like will use pyinstaller to create a .exe and a wheel for distribution
# more details at: https://packaging.python.org/overview/

import time, os, sys, math, pickle, pygame
import numpy as np
from tensorflow import keras
from collections import deque
from pygame.locals import *
from pynput.keyboard import Key, Controller


# Global Variables - Should Not Change
keyboard = Controller()
screen_height = 800
number_of_columns = 10
number_of_rows = 40
screen_width = int(screen_height / 4)
tetromino_start_x = int(screen_width / 2) - int(screen_width / number_of_columns)
tetromino_start_y = int(screen_height / number_of_rows)
fpsclock = pygame.time.Clock()


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
    def __init__(self, tetrominotype):
        super(Tetromino, self).__init__()
        self.bricks = []
        self.leftEdge = False
        self.rightEdge = False
        self.wallOverlap = False
        self.type = tetrominotype
        self.rotationAngle = 0
        if tetrominotype == 0:  # 0.Square. No Rotation or Variants so no function required
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

    def rotate(self):  # Calling this with 270 will draw a new piece. THIS IS INCOMPLETE
        # Stop handling inputs until this is done
        pygame.event.set_blocked(pygame.KEYDOWN)
        pygame.event.set_blocked(pygame.KEYUP)

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
        pygame.event.set_allowed(pygame.KEYDOWN)
        pygame.event.set_allowed(pygame.KEYUP)

    def update(self, pressed_keys, wall, score, number_of_rows_with_no_downkey):
        # Stop handling inputs until this is done
        pygame.event.set_blocked(pygame.KEYDOWN)
        pygame.event.set_blocked(pygame.KEYUP)

        self.leftEdge = False
        self.rightEdge = False
        # Left and Right also need something to stop them moving when they hit the bottom.
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
        pygame.event.set_allowed(pygame.KEYDOWN)
        pygame.event.set_allowed(pygame.KEYUP)
        return score

    def drop_tetromino(self, wall):
        # Stop handling inputs until this is done
        pygame.event.set_blocked(pygame.KEYDOWN)
        pygame.event.set_blocked(pygame.KEYUP)
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
        pygame.event.set_allowed(pygame.KEYDOWN)
        pygame.event.set_allowed(pygame.KEYUP)


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

        # Build and Display Wall Brick Count Array
        for i in range(0, number_of_rows):
            for brick in self.bricks:
                if brick.Ycoord == screen_height - (i + 1) * int(screen_width / number_of_columns):
                    self.bricksperLine[i] = self.bricksperLine[i] + 1

        # Check for GameOver due to too many rows
        if self.bricksperLine[number_of_rows - 1] > 0:
            return -1

        # Search for and remove Complete Rows
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

        # Drop Down Lines left after complete lines have been removed
        if len(self.completeRows) > 0:
            for rows in range(len(self.completeRows) - 1, -1, -1):
                j = self.completeRows[rows] + 1
                for brick in self.bricks:
                    if brick.Ycoord < screen_height - j * int(screen_width / number_of_columns):
                        brick.Ycoord = brick.Ycoord + int(screen_height / number_of_rows)
                        brick.rect.y = brick.Ycoord
                        brick.bottom = int(brick.Ycoord + screen_width / number_of_columns)
        return score


class Brain:
    def __init__(self):
        self.epsilon = 0.05  # This is the epsilon for the greedy algorithm.
        self.outputs = 5
        self.root_logdir = os.path.join(os.curdir, "Tetris_RL_Model_Logs")
        self.root_resultdir = os.path.join(os.curdir, "Tetris_RL_Result_Logs")
        self.dequefile = os.path.join(self.root_logdir, "PickledDeque.obj")

        # Check if a file called LatestTrainedModel.h5 exists, otherwise create the model
        if os.path.exists(os.path.join(self.root_logdir, "LatestTrainedModel.h5")):
            self.model = keras.models.load_model(os.path.join(self.root_logdir, "LatestTrainedModel.h5"))
        else:
            input_ = keras.layers.Input(shape=[(number_of_rows * number_of_columns) + 8])
            tetrominoinput_ = keras.layers.Input(shape=[8])
            hidden1 = keras.layers.Dense(300, activation="relu")(input_)
            hidden2 = keras.layers.Dense(300, activation="relu")(hidden1)
            concat = keras.layers.Concatenate()([tetrominoinput_, hidden2])
            output = keras.layers.Dense(self.outputs, activation="softmax")(concat)
            self.model = keras.Model(inputs=[input_, tetrominoinput_], outputs=[output])

        # Create or reload a replay buffer
        if os.path.exists(self.dequefile):
            self.replay_buffer = deque(maxlen=2000)
            self.replay_buffer = pickle.load(open(self.dequefile, 'rb'))
        else:
            self.replay_buffer = deque(maxlen=2000)

    def makeamove(self, totalstatematrix, flattetrominostatematrix):
        keyboard.release(Key.space)
        keyboard.release(Key.right)
        keyboard.release(Key.left)
        keyboard.release(Key.down)
        keyboard.release('z')

        # epsilon greedy algorithm
        if np.random.rand() < self.epsilon:  # Make a random move epsilon of the time
            outputdecision = np.random.randint(self.outputs)
        else:  # Make a move as specified by the DQN
            q_values = self.model.predict((totalstatematrix[np.newaxis], flattetrominostatematrix[np.newaxis]))
            outputdecision = np.argmax(q_values[0])

        # Make our Move
        if outputdecision == 0:
            keyboard.press(Key.space)
        elif outputdecision == 1:
            keyboard.press(Key.right)
        elif outputdecision == 2:
            keyboard.press(Key.left)
        elif outputdecision == 3:
            keyboard.press(Key.down)
        elif outputdecision == 4:
            keyboard.press('z')

        return outputdecision

    def updatebrain(self):
        batch_size = 32
        discount_factor = 0.95
        optimizer = keras.optimizers.Adam(lr=1e-3)
        loss_fn = keras.losses.mean_squared_error
        indices = np.random.randint(len(self.replay_buffer), size=32)  # Sampling 32 from the buffer at a time
        batch = [self.replay_buffer[index] for index in indices]
        #print(batch[0])
        # structre above is [array[400],array[8]], int, int, [array[400],array[8]], bool
        # This bit is going to take a proper understanding of np.
        # retrain_state_input[np.newaxis], retrain_tetromino_input[np.newaxis], retrain_action, retrain_score, retrain_state_output[np.newaxis], retrain_tetromino_output[np.newaxis], retrain_done = [np.array([experience[field_index] for experience in batch]) for field_index in range(5)]
        # experiences = [np.array([experience[field_index] for experience in batch]) for field_index in range(5)]
        # retrain_state_input, retrain_action, retrain_score, retrain_state_output, retrain_done = experiences
        # next_Q_values = model.predict((retrain_state_input[np.newaxis], retrain_tetromino_input[np.newaxis]))
        # max_next_Q_values = np.max(next_Q_values, axis = 1)
        # target_Q_values = (retrain_score + (1 - retrain_done) * 0.95 * max_next_Q_values)
        # target_Q_values = target_Q_values.reshape(-1,1)
        # mask = tf.one_hot(retrain_action, brainoutputoptions)
        # End of DCN Update so we can start a new game
        #return 1

class TetrisApp(pygame.sprite.Sprite):
    def __init__(self):
        # Graphics Params
        self.screen_Caption = "Tetris"
        self.number_of_rows_with_no_downkey = 2
        self.rng1 = np.random.RandomState()
        pygame.init()
        self.screen_dim = (screen_width, screen_height)  # Screen Size
        self.screen = pygame.display.set_mode(self.screen_dim)
        self.screen_bg_colour = (0, 0, 0)
        self.screen.fill(self.screen_bg_colour)
        self.drop_Tetromino = pygame.USEREVENT + 1
        self.initialiseparameters()
        self.activeGame = False
        pygame.time.set_timer(self.drop_Tetromino, self.drop_Tetromino_speed)
        self.gamesplayed = 0
        self.player = "Human"  # "Human"
        self.paused = False
        self.logssaved = False
        self.training = False
        self.gamestoplayintraining = 3
        self.brain = Brain()
        super(TetrisApp, self).__init__()

    def handleevents(self): # This has been tidied up
        # Handle Quit and drop timer
        for event in pygame.event.get():
            if event.type == QUIT:  # This may need to be adjusted for automated re-starts. same as game over trigger
                sys.exit()
            elif event.type == self.drop_Tetromino and self.paused is False:
                self.tetromino.drop_tetromino(self.tetris_Wall)

        # Handle inputs for the game and pass Tetromino moves to the Tetromino object
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_n]:
            self.logssaved = False
            self.player = "Human"
            self.gamesplayed = 0
            self.initialiseparameters()
            self.activeGame = True

        if pressed_keys[K_m]:
            self.player = "Machine"
            self.gamesplayed = 0
            self.initialiseparameters()
            self.activeGame = True

        if pressed_keys[K_t]:
            self.player = "Machine"
            self.training = True
            self.gamesplayed = 0
            self.initialiseparameters()
            self.activeGame = True

        if pressed_keys[K_p]:
            self.paused = not self.paused

        if pressed_keys[K_q]:
            self.activeGame = False

        if pressed_keys[K_e]:
            exit()

        if self.paused is False and self.activeGame is True:  # Update based on key moves
            self.updateactivegame(pressed_keys)
        elif not self.activeGame:
            print(self.gamesplayed)
            print(self.gamestoplayintraining)
            print(self.training)
            if self.training is True and self.gamesplayed < self.gamestoplayintraining:  # Update training model
                print("In the update")
                self.brain.updatebrain()
                self.gamesplayed = self.gamesplayed + 1
                self.initialiseparameters()
                self.activeGame = True
                pygame.time.set_timer(self.drop_Tetromino, self.drop_Tetromino_speed)
            else:
                self.restartscreen()

    def updateactivegame(self, pressed_keys):
        if self.player == "Machine" and self.paused is False and self.activeGame is True:
            # Need to generate a flattened array here of the Screen Status (0 - empty, 1 = wall or tetromino block)
            # Also generating a flattened array of the Tetromino x,y cooords
            statematrix = np.zeros((number_of_rows, number_of_columns))
            tetrominolist = []

            # Generate Wall State Matrix (including Tetromino)
            for brick in self.tetromino.bricks:
                statematrix[int(brick.Ycoord / 20), int(brick.Xcoord / 20)] = 1
            for brick in self.tetris_Wall.bricks:
                statematrix[int(brick.Ycoord / 20), int(brick.Xcoord / 20)] = 1
            flatstatematrix = statematrix.flatten()

            # Generate Tetromino State
            for brick in self.tetromino.bricks:
                tetrominolist.append(brick.Xcoord)
                tetrominolist.append(brick.Ycoord)

            # Flatten and append
            tetrominostatematrix = np.array(tetrominolist)
            flattetrominostatematrix = tetrominostatematrix.flatten()
            totalstatematrix = np.concatenate((flatstatematrix, flattetrominostatematrix))

            # Pass to DQN to make a move
            brainbuttonpress = self.brain.makeamove(totalstatematrix, flattetrominostatematrix)

        pygame.event.set_blocked(pygame.KEYUP)
        pygame.event.set_blocked(pygame.KEYDOWN)
        previousscore = self.score
        self.score = self.tetromino.update(pressed_keys, self.tetris_Wall, self.score,
                                           self.number_of_rows_with_no_downkey)
        score_candidate = self.tetris_Wall.clearlines(self.level, self.score)
        if score_candidate == -1:
            if self.gamesplayed < self.gamestoplayintraining:
                run_id = time.strftime("run_%Y_%m_%d-%H_%M_%S.h5")
                self.brain.model.save(os.path.join(self.brain.root_logdir, run_id))
            else:
                self.brain.model.save(os.path.join(self.brain.root_logdir, "LatestTrainedModel.h5"))
                if self.training:
                    pickle.dump(self.brain.replay_buffer, open(self.brain.dequefile,'wb'))
            self.activeGame = False
            self.logssaved = True
        else:
            self.score = score_candidate

        if self.tetromino.wallOverlap is True:
            self.tetromino_Count = self.tetromino_Count + 1
            tetromino_type = self.tetromino_Index[self.tetromino_Count % 7]
            self.tetromino = Tetromino(tetromino_type)
            if (self.tetromino_Count % 7) == 6:
                self.rng1.shuffle(self.tetromino_Index)
            for brick in self.tetromino.bricks:
                for wallBrick in self.tetris_Wall.bricks:
                    if brick.rect.x == wallBrick.rect.x:
                        if brick.rect.y == wallBrick.rect.y:
                            self.tetromino.wallOverlap = True
                            if self.gamesplayed < self.gamestoplayintraining:
                                run_id = time.strftime("run_%Y_%m_%d-%H_%M_%S.h5")
                                self.brain.model.save(os.path.join(self.brain.root_logdir, run_id))
                            else:
                                self.brain.model.save(os.path.join(self.brain.root_logdir, "LatestTrainedModel.h5"))
                                if self.training:
                                    pickle.dump(self.brain.replay_buffer, open(self.brain.dequefile,'wb'))
                            self.logssaved = True
                            self.activeGame = False

        # Redraw, so clear screen, fill background, redraw wall and redraw tetromino
        if self.activeGame is True:
            self.screen.fill(self.screen_bg_colour)

        # Display Score
        msg = "Score: " + str(self.score)
        msg_color = (255, 255, 255)
        f = pygame.font.SysFont('arial', 12)
        msg_image = f.render(msg, True, msg_color, None)
        scoresurf = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        scorerect = scoresurf.get_rect()
        scorerect.x = 135
        scorerect.y = 0
        self.screen.blit(msg_image, scorerect)

        # Display Level
        if math.floor(int(time.time() - self.s) / int(self.level_speed_rate)) > self.level:
            self.level += 1
            self.drop_Tetromino_speed -= self.drop_Tetromino_speed_rate
            pygame.time.set_timer(self.drop_Tetromino, max(self.drop_Tetromino_speed, 1))

        level_msg = "Level: " + str(self.level)
        level_msg_color = (255, 255, 0)
        g = pygame.font.SysFont('arial', 12)
        level_msg_image = g.render(level_msg, True, level_msg_color, None)
        levelsurf = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
        levelrect = levelsurf.get_rect()
        levelrect.x = 0
        levelrect.y = 0
        self.screen.blit(level_msg_image, levelrect)

        # Display Score
        if self.training is True:
            msg = "Game: " + str(self.gamesplayed)
            msg_color = (0, 255, 255)
            f = pygame.font.SysFont('arial', 12)
            msg_image = f.render(msg, True, msg_color, None)
            gamessurf = pygame.Surface((20, 5), pygame.SRCALPHA, 32)
            gamesrect = gamessurf.get_rect()
            gamesrect.x = 75
            gamesrect.y = 0
            self.screen.blit(msg_image, gamesrect)

        # Draw Bricks and Draw Wall
        if self.activeGame is True:
            for brick in self.tetromino.bricks:
                brick.rect.x = brick.Xcoord
                brick.rect.y = brick.Ycoord
                self.screen.blit(brick.surf, brick.rect)
            for brick in self.tetris_Wall.bricks:
                self.screen.blit(brick.surf, brick.rect)

        # Creating the Post state matrices
        if self.player == "Machine" and self.paused is False and self.activeGame is True:
            poststatematrix = np.zeros((number_of_rows, number_of_columns))
            posttetrominolist = []

            # Generate Wall State Matrix (including Tetromino)
            for brick in self.tetromino.bricks:
                poststatematrix[int(brick.Ycoord / 20), int(brick.Xcoord / 20)] = 1
            for brick in self.tetris_Wall.bricks:
                poststatematrix[int(brick.Ycoord / 20), int(brick.Xcoord / 20)] = 1
            postflatstatematrix = poststatematrix.flatten()

            # Generate Tetromino State
            for brick in self.tetromino.bricks:
                posttetrominolist.append(brick.Xcoord)
                posttetrominolist.append(brick.Ycoord)

            # Flatten and append
            posttetrominostatematrix = np.array(posttetrominolist)
            postflattetrominostatematrix = posttetrominostatematrix.flatten()
            posttotalstatematrix = np.concatenate((postflatstatematrix, postflattetrominostatematrix))

            self.brain.replay_buffer.append(((flatstatematrix[np.newaxis], flattetrominostatematrix[np.newaxis]), brainbuttonpress, self.score - previousscore, (posttotalstatematrix[np.newaxis], postflattetrominostatematrix[np.newaxis]), not(self.activeGame)))

        pygame.event.set_allowed(pygame.KEYUP)
        pygame.event.set_allowed(pygame.KEYDOWN)

    def restartscreen(self):
        oldscore = self.score
        oldlevel = self.level
        oldcount = self.tetromino_Count
        self.screen.fill(self.screen_bg_colour)
        start_msg1 = "(N)ew/(M)achine/(T)rain"
        start_msg1_color = (255, 0, 0)
        start_msg2 = "Tetrominos: " + str(oldcount)
        start_msg2_color = (255, 255, 255)
        start_msg3 = "Level: " + str(oldlevel)
        start_msg3_color = (255, 255, 255)
        start_msg4 = "Score: " + str(oldscore)
        start_msg4_color = (255, 255, 255)
        g = pygame.font.SysFont('arial', 12)  # - math.ceil(800/screen_height))
        g2 = pygame.font.SysFont('arial', 16)  # - math.ceil(800/screen_height))
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
        startrect1.x, startrect1.y = 10, 400
        self.screen.blit(start_msg1_image, startrect1)
        startrect2.x,startrect2.y = 30, 440
        self.screen.blit(start_msg2_image, startrect2)
        startrect3.x, startrect3.y = 30, 480
        self.screen.blit(start_msg3_image, startrect3)
        startrect4.x, startrect4.y = 30, 520
        self.screen.blit(start_msg4_image, startrect4)

    def initialiseparameters(self): # To prevent multiple similar calls
        keyboard.release(Key.space)
        keyboard.release(Key.right)
        keyboard.release(Key.left)
        keyboard.release(Key.down)
        keyboard.release('z')
        self.s = time.time()
        self.drop_Tetromino_speed = 500  # Reduce this for a faster game especially when in Machine Mode
        self.drop_Tetromino_speed_rate = 10
        self.level_speed_rate = 45
        self.FPS = 10
        self.tetromino_Index = [0, 1, 2, 3, 4, 5, 6]
        self.rng1.shuffle(self.tetromino_Index)
        self.tetromino = Tetromino(self.tetromino_Index[0])
        self.tetris_Wall = WallClass()
        self.score = 0
        self.level = 0
        self.tetromino_Count = 0


def play_tetris():
    tetrisapp = TetrisApp()
    # Main Program Loop
    while True:
        tetrisapp.handleevents()
        pygame.display.flip()
        fpsclock.tick(tetrisapp.FPS)

play_tetris()