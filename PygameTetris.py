#! /usr/bin/env python
# -*- coding: utf-8 -*-
#A Pygame Implementation of Tetris
#Author: Billy Donegan (billydonegan76)
#Date 12/05/2020
#To Do:
#--------- GAME  5 Bugs :( ---------------------------
#FIXED - Handle issue with rotation into Wall which creates >10 items per line and then everything breaks
#FIXED - Putting a Tetromino under a line makes it stop which is wrong; it should continue to drop
#TO FIX - Ceiling Bug where not checking overlap for created Tetromino
#TO FIX - Rare glitch with rotating at very bottom
#TO FIX - Tetromino not working either e.g 10,10,10,10,9,7,3 -> 9,10 -> 9 which is not right
#TO FIX - Screen size is not changing based on screen_height (HOME SCREEN WORKS NOW)
#TO FIX - Rotation at right edge of screen fails for resizing (e.g. 400)
#Optional - Add a ghost Tetromino

#-------- Machine Learning -------------------------
#Want a neural network with parameters that takes in the current state and returns a value 0 - 4
#Initiation of parameters can be random initially but needs to be read from a File
#DONE - Moving based on that number is implemented

#-------- Machine Learning Training ----------------
#Key Expectation for training is that this must ultimately be able to run without screen (but can show the game progressing)
#Can be considered a function that takes a seed, sequence of inputs and returns a score.
#Will aim to wrap in a Reinforcement Learning Process for AI Tetris Player (but one step at a time...)
#Incrementing of parameters is part of training and needs to be output as a File

#------- Porting To Android-----------------
#Port to Kivy
#Last Step: Turn into a callable function with graphics switchable on or off
#DONE - Accept inputs from code not from keys
#---------Cloud Connectivity for Training?---------------
import time, collections
import numpy as np
import sys
import math
import random
import pygame
from pygame.locals import *
import pynput
from pynput.keyboard import Key, Controller

keyboard = Controller()

#Global Variables - Should Not Change
screen_height = 800
number_of_columns = 10
number_of_rows = 40
screen_width = int(screen_height/4)
tetromino_start_x = int(screen_width/2) - int(screen_width/number_of_columns)
tetromino_start_y = int(screen_height/number_of_rows)

#Timers
fpsclock = pygame.time.Clock()
s=time.time()

#Create Classes:
class Brain():
	def __init__(self, BrainOutputOptions):
		self.Output_options = BrainOutputOptions
		self.key = []

	def MakeAMove(self):
		keyboard.release(Key.space)
		keyboard.release(Key.right)
		keyboard.release(Key.left)
		keyboard.release(Key.down)
		keyboard.release('z')
		self.key = random.randint(0, self.Output_options)
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

class generic_Brick(pygame.sprite.Sprite):
    def __init__(self, X, Y, R, G, B, O):
        super(generic_Brick, self).__init__()
        self.surf = pygame.Surface((screen_width/number_of_columns, screen_width/number_of_columns))
        self.surf.fill((R,G,B))
        self.rect = self.surf.get_rect()
        self.rect.x = X
        self.rect.y = Y
        self.Xcoord = X
        self.Ycoord = Y
        self.red = R
        self.green = G
        self.blue = B
        self.origin = O
        self.bottom = int(self.Ycoord + screen_width/number_of_columns)

class Tetromino():
    def __init__(self, type, ghostFlag):
        super(Tetromino, self).__init__()
        self.bricks = []
        self.leftEdge = False
        self.rightEdge = False
        self.wallOverlap = False
        self.ghost = ghostFlag
        self.type = type
        self.rotationAngle = 0
        if type == 0: #0 . No Rotation or Variants so no function required
            self.bricks.append(generic_Brick(tetromino_start_x,tetromino_start_y,255,255,0, True))
            self.bricks.append(generic_Brick(tetromino_start_x + int(screen_width/number_of_columns),tetromino_start_y,255,255,0, False))
            self.bricks.append(generic_Brick(tetromino_start_x,tetromino_start_y + int(screen_height/number_of_rows),255,255,0, False))
            self.bricks.append(generic_Brick(tetromino_start_x + int(screen_width/number_of_columns),tetromino_start_y + int(screen_height/number_of_rows),255,255,0, False))
        else:
        	self.rotationAngle = 270 #Just trigger a rotation to 0 to draw a new Tetromino in place.
        	self.rotate()

    def rotate(self): #Calling this with 270 will draw a new piece
        self.rotationAngle = (self.rotationAngle + 90) % 360
        if self.bricks == []:
            x = tetromino_start_x
            y = tetromino_start_y #If this is a new Tetromino set the Origin Block
        for brick in self.bricks: #This moves the origin block for some specific scenarios of J,L and I
            if brick.origin == True:
                if self.type ==1 and (self.rotationAngle == 90 or self.rotationAngle == 270):
                	x = brick.Xcoord + int(screen_width/number_of_columns)
                	y = brick.Ycoord
                if self.type ==1 and (self.rotationAngle == 0 or self.rotationAngle == 180):
                	x = brick.Xcoord - int(screen_width/number_of_columns)
                	y = brick.Ycoord
                else:
                	x = brick.Xcoord
                	y = brick.Ycoord

		#Need to handle wall events now too
        if self.type == 1: #I
    	    if self.rotationAngle == 0 or self.rotationAngle == 180:
    	        if x - int(screen_width/number_of_columns) >= 0 and x + int(screen_width/number_of_columns) <= 160:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x,y,0,255,255, True))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,0,255,255, True))
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y,0,255,255, False))
    	            self.bricks.append(generic_Brick(x + 2*int(screen_width/number_of_columns),y,0,255,255, False))
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 90 or self.rotationAngle == 270:
    	        if y < screen_height - 2*int(screen_width/number_of_columns):
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x,y,0,255,255, True))
    	            self.bricks.append(generic_Brick(x,y + int(screen_height/number_of_rows),0,255,255, False))
    	            self.bricks.append(generic_Brick(x,y - int(screen_height/number_of_rows),0,255,255, False))
    	            self.bricks.append(generic_Brick(x,y + 2*int(screen_height/number_of_rows),0,255,255, False))
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
        elif self.type == 2: #Z
    	    if self.rotationAngle == 0 or self.rotationAngle == 180:
    	        if x - int(screen_width/number_of_columns) >= 0:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y,255,0,0, False))
    	            self.bricks.append(generic_Brick(x, y,255,0,0, True))
    	            self.bricks.append(generic_Brick(x, y + int(screen_height/number_of_rows),255,0,0, False))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y + int(screen_height/number_of_rows),255,0,0, False))
    	    elif self.rotationAngle == 90 or self.rotationAngle == 270:
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,255,0,0, False))
    	        self.bricks.append(generic_Brick(x, y,255,0,0, True))
    	        self.bricks.append(generic_Brick(x, y + int(screen_height/number_of_rows),255,0,0, False))
    	        self.bricks.append(generic_Brick(x + 1*int(screen_width/number_of_columns),y - int(screen_height/number_of_rows),255,0,0, False))
        elif self.type == 3: #S
    	    if self.rotationAngle == 0 or self.rotationAngle == 180:
    	        if x - int(screen_width/number_of_columns) >= 0:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,0,255,0, False))
    	            self.bricks.append(generic_Brick(x , y,0,255,0, True))
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns) ,y + int(screen_height/number_of_rows),0,255,0, False))
    	            self.bricks.append(generic_Brick(x,y + int(screen_height/number_of_rows),0,255,0, False))
    	    elif self.rotationAngle == 90 or self.rotationAngle == 270:
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x,y,0,255,0, True))
    	        self.bricks.append(generic_Brick(x + 1*int(screen_width/number_of_columns), y,0,255,0, False))
    	        self.bricks.append(generic_Brick(x + 1*int(screen_width/number_of_columns) ,y + int(screen_height/number_of_rows),0,255,0, False))
    	        self.bricks.append(generic_Brick(x,y -1*int(screen_height/number_of_rows),0,255,0, False))
        elif self.type == 4: #T
    	    if self.rotationAngle == 0:
    	        if x < 180:
    	            #	1
    	            #2	0	3
    	            #
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x,y - int(screen_height/number_of_rows),128,0,128, False)) #1
    	            self.bricks.append(generic_Brick(x,y,128,0,128, True)) #0
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,128,0,128, False)) #3
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y,128,0,128, False)) #2
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 90:
    	        #	1
    	        #	0	3
    	        #	4
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x,y - int(screen_height/number_of_rows),128,0,128, False)) #1
    	        self.bricks.append(generic_Brick(x,y,128,0,128, True)) #0
    	        self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,128,0,128, False)) #3
    	        self.bricks.append(generic_Brick(x,y + int(screen_height/number_of_rows),128,0,128, False)) #4
    	    elif self.rotationAngle == 180:
    	        if x > 0:
    	            #
    	            #2	0	3
    	            #	4
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y,128,0,128, False)) #2
    	            self.bricks.append(generic_Brick(x,y,128,0,128, True)) #0
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,128,0,128, False)) #3
    	            self.bricks.append(generic_Brick(x,y + int(screen_height/number_of_rows),128,0,128, False)) #4
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 270:
    	        #	1
    	        #2	0
    	        #	4
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x,y - int(screen_height/number_of_rows),128,0,128, False)) #1
    	        self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y,128,0,128, False)) #2
    	        self.bricks.append(generic_Brick(x,y,128,0,128, True)) #0
    	        self.bricks.append(generic_Brick(x,y + int(screen_height/number_of_rows),128,0,128, False)) #4
        elif self.type == 5: #L
    	    if self.rotationAngle == 0:
    	        if x < 180:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,255,165,0, False))
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns) ,y + 1*int(screen_height/number_of_rows),255,165,0, False))
    	            self.bricks.append(generic_Brick(x,y + 1*int(screen_height/number_of_rows),255,165,0, True))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y + 1*int(screen_height/number_of_rows),255,165,0, False))
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 90:
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x,y,255,165,0, False))
    	        self.bricks.append(generic_Brick(x,y - 1*int(screen_height/number_of_rows),255,165,0, False))
    	        self.bricks.append(generic_Brick(x,y - 2*int(screen_height/number_of_rows),255,165,0, True))
    	        self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y,255,165,0, False))
    	    elif self.rotationAngle == 180:
    	        if x > 0:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y + 2*int(screen_height/number_of_rows),255,165,0, False))
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y+ 1*int(screen_height/number_of_rows),255,165,0, True))
    	            self.bricks.append(generic_Brick(x,y+ 1*int(screen_height/number_of_rows),255,165,0, False))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y+ 1*int(screen_height/number_of_rows),255,165,0, False))
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 270:
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x+ int(screen_width/number_of_columns),y - 1*int(screen_height/number_of_rows),255,165,0, False))
    	        self.bricks.append(generic_Brick(x+ int(screen_width/number_of_columns),y,255,165,0, True))
    	        self.bricks.append(generic_Brick(x+ int(screen_width/number_of_columns),y + 1*int(screen_height/number_of_rows),255,165,0, False))
    	        self.bricks.append(generic_Brick(x,y - 1*int(screen_height/number_of_rows),255,165,0, False))
        elif self.type == 6: #J
    	    if self.rotationAngle == 0:
    	        if x < 180:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y,0,0,255, False))
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y + 1*int(screen_height/number_of_rows),0,0,255, False))
    	            self.bricks.append(generic_Brick(x ,y + 1*int(screen_height/number_of_rows),0,0,255, True))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y + 1*int(screen_height/number_of_rows),0,0,255, False))
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 90:
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x+ int(screen_width/number_of_columns),y - 2*int(screen_height/number_of_rows),0,0,255, False))
    	        self.bricks.append(generic_Brick(x,y - 2*int(screen_height/number_of_rows),0,0,255, True))
    	        self.bricks.append(generic_Brick(x,y - int(screen_height/number_of_rows),0,0,255, False))
    	        self.bricks.append(generic_Brick(x,y,0,0,255, False))
    	    elif self.rotationAngle == 180:
    	        if x > 0:
    	            self.bricks = []
    	            self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y+ 1*int(screen_height/number_of_rows) ,0,0,255, False))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y + 2*int(screen_height/number_of_rows),0,0,255, False))
    	            self.bricks.append(generic_Brick(x,y+ 1*int(screen_height/number_of_rows),0,0,255, True))
    	            self.bricks.append(generic_Brick(x + int(screen_width/number_of_columns),y+ 1*int(screen_height/number_of_rows) ,0,0,255, False))
    	        else:
    	            self.rotationAngle = (self.rotationAngle - 90) % 360
    	    elif self.rotationAngle == 270:
    	        self.bricks = []
    	        self.bricks.append(generic_Brick(x,y - 1*int(screen_height/number_of_rows),0,0,255, False))
    	        self.bricks.append(generic_Brick(x,y,0,0,255, True))
    	        self.bricks.append(generic_Brick(x,y + 1*int(screen_height/number_of_rows),0,0,255, False))
    	        self.bricks.append(generic_Brick(x - int(screen_width/number_of_columns),y + 1*int(screen_height/number_of_rows),0,0,255, False))

    def update(self, pressed_keys, Wall, score, level, number_Of_Rows_With_No_Downkey):
        self.leftEdge = False
        self.rightEdge = False

		#Left and Right need something to stop them moving when they hit the bottom. That will solve most of the issue
        if pressed_keys[K_LEFT]:
            for brick in self.bricks:
                if brick.rect.left <= 0:
                    self.leftEdge = True
                for wallBrick in Wall.bricks:
                    if brick.Xcoord - int(screen_width/number_of_columns) == wallBrick.Xcoord:
                        if brick.Ycoord == wallBrick.Ycoord:
                            self.leftEdge = True
            if self.leftEdge == False and self.wallOverlap == False:
                for brick in self.bricks:
                    brick.Xcoord = brick.Xcoord - int(screen_width/number_of_columns)
                    brick.rect.x = brick.Xcoord

        if pressed_keys[K_RIGHT]:
            for brick in self.bricks:
                if brick.rect.right >= screen_width:
                    self.rightEdge = True
                for wallBrick in Wall.bricks:
                    if brick.Xcoord + int(screen_width/number_of_columns) == wallBrick.Xcoord:
                        if brick.Ycoord == wallBrick.Ycoord:
                            self.rightEdge = True
            if self.rightEdge == False and self.wallOverlap == False:
                for brick in self.bricks:
                    brick.Xcoord = brick.Xcoord + int(screen_width/number_of_columns)
                    brick.rect.x = brick.Xcoord

        if pressed_keys[K_DOWN]:
            for brick in self.bricks:
                if brick.Ycoord >  number_Of_Rows_With_No_Downkey*int(screen_height/number_of_rows):
                    while self.wallOverlap == False:
                        self.drop_Tetromino(Wall)
                        score += 1

        if pressed_keys[K_SPACE]:
            self.rotate()

        if pressed_keys[K_z]:
            self.drop_Tetromino(Wall)
            score += 1

        return score

    def drop_Tetromino(self, Wall):
        for brick in self.bricks:
            if brick.bottom >= screen_height:
                self.wallOverlap = True
            for wallBrick in Wall.bricks:
                if brick.Xcoord == wallBrick.Xcoord:
                    if brick.Ycoord + int(screen_height/number_of_rows) == wallBrick.Ycoord:
                        self.wallOverlap = True
        if self.wallOverlap == True:
            for brick in self.bricks:
                New_Brick = generic_Brick(brick.Xcoord,brick.Ycoord, brick.red, brick.green, brick.blue, False)
                Wall.bricks.append(New_Brick)
        elif self.wallOverlap == False:
            for brick in self.bricks:
                brick.Ycoord = brick.Ycoord + int(screen_height/number_of_rows)
                brick.rect.y = brick.Ycoord
                brick.bottom = int(brick.Ycoord + screen_width/number_of_columns)

class wallClass():
    def __init__(self):
        self.bricks = []
        self.bricksperLine = []
        self.completeRows = []
        self.tooHigh = False
        super(wallClass, self).__init__()

    def clearLines(self, level, score):

    	#Initialise
    	self.bricksperLine = [0]*(number_of_rows)
    	self.completeRows = []
    	i = 0

    	#Build Wall Brick Count Array
    	for i in range(0,number_of_rows):
    	    for brick in self.bricks:
    	        if brick.Ycoord == screen_height - (i+1)*int(screen_width/number_of_columns):
    	            self.bricksperLine[i] =  self.bricksperLine[i] + 1

    	print(self.bricksperLine) #THIS WILL TELL YOU WHEN THE ISSUE IS RESOLVED. ONLY DOWN TO ROTATION NOW

    	#Check for GameOver print(self.bricksperLine)
    	if self.bricksperLine[number_of_rows-1] > 0:
    	    return -1

		#Search for and remove Complete Rows
    	for i in range(0,number_of_rows):
    	    if self.bricksperLine[i] >= number_of_columns:
    	        self.bricks = [brick for brick in self.bricks if brick.Ycoord !=(screen_height - (i+1)*int(screen_width/number_of_columns))]
    	        self.completeRows.append(i)

    	if len(self.completeRows) == 1:
    		score += 40*(level + 1)
    	elif len(self.completeRows) == 2:
    		score += 100*(level + 1)
    	elif len(self.completeRows) == 3:
    		score += 300*(level + 1)
    	elif len(self.completeRows) == 4:
    		score += 1200*(level + 1)

    	#Drop Down Lines
    	while len(self.completeRows) > 0:
    	    for i in range(self.completeRows[-1]+1,number_of_rows):
    	        for brick in self.bricks:
    	            if brick.Ycoord < screen_height - (i)*int(screen_width/number_of_columns):
    	        	    brick.Ycoord = brick.Ycoord + int(screen_height/number_of_rows)
    	        	    brick.rect.y = brick.Ycoord
    	        	    brick.bottom = int(brick.Ycoord + screen_width/number_of_columns)
    	    self.completeRows.pop(-1)
    	return score

class TetrisGame(pygame.sprite.Sprite):
    def __init__(self):
        self.drop_Tetromino_speed = 500
        self.drop_Tetromino_speed_rate = 10
        self.level_speed_rate = 45
        self.FPS = 10
        self.screen_Caption = "Tetris"
        self.number_Of_Rows_With_No_Downkey = 3
        self.seed = 1234 #Can be randomised if needed
        pygame.init()
        self.screen_dim = (screen_width,screen_height) #Screen Size
        self.screen = pygame.display.set_mode(self.screen_dim)
        self.screen_bg_colour = (0,0,0)
        self.screen.fill(self.screen_bg_colour)
        self.drop_Tetromino = pygame.USEREVENT + 1
        pygame.time.set_timer(self.drop_Tetromino, self.drop_Tetromino_speed)
        self.tetromino_Count = 0
        self.score = 0
        self.level = 0
        self.paused = False
        self.activeGame = False
        self.player = "Human" #"Human"
        self.tetromino_Index = [0,1,2,3,4,5,6]
        random.Random(self.seed).shuffle(self.tetromino_Index)
        #Instantiate our Tetromino - A wall, a tetromino
        self.tetromino = Tetromino(self.tetromino_Index[0], False)
        self.ghost_tetromino = Tetromino(self.tetromino_Index[0], False)
        self.rotation_test_tetromino = Tetromino(self.tetromino_Index[0], False)
        self.tetris_Wall = wallClass() # For drawing target location of Tetromino
        self.Brain = Brain(4)
        super(TetrisGame, self).__init__()

    def handleEvents(self):
	    #Handle Quit and drop timer
	    for event in pygame.event.get():
	        if event.type == QUIT: #This may need to be adjusted for automated re-starts. same as game over trigger
	            sys.exit()
	        elif(event.type == self.drop_Tetromino and self.paused == False):
	            self.tetromino.drop_Tetromino(self.tetris_Wall)

	    if self.player == "Machine":
	    	Brain.MakeAMove(self.Brain)

	    #Handle inputs for the game and pass Tetromino moves to the Tetromino object
	    pressed_keys = pygame.key.get_pressed()
	    if pressed_keys[K_n]:
	        print("New Game!")
	        keyboard.release(Key.space)
	        keyboard.release(Key.right)
	        keyboard.release(Key.left)
	        keyboard.release(Key.down)
	        keyboard.release('z')
	        #Instantiate our Tetromino for next game
	        self.tetromino_Index = [0,1,2,3,4,5,6]
	        random.Random(self.seed).shuffle(self.tetromino_Index)
	        #random.shuffle(tetromino_Index)
	        self.tetromino = Tetromino(self.tetromino_Index[0], False)
	        self.tetris_Wall = wallClass()
	        self.score = 0
	        self.level = 0
	        self.tetromino_Count = 0
	        self.activeGame = True
	        self.player = "Human"

	    if pressed_keys[K_m]:
	        print("New Machine Game!")
	        #Instantiate our Tetromino for next game
	        self.tetromino_Index = [0,1,2,3,4,5,6]
	        random.Random(self.seed).shuffle(self.tetromino_Index)
	        #random.shuffle(tetromino_Index)
	        self.tetromino = Tetromino(self.tetromino_Index[0], False)
	        self.tetris_Wall = wallClass()
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

    def updateActiveGame(self, pressed_keys):
        self.score = self.tetromino.update(pressed_keys, self.tetris_Wall, self.score, self.level, self.number_Of_Rows_With_No_Downkey)
        score_candidate = self.tetris_Wall.clearLines(self.level, self.score)
        if score_candidate == -1:
            self.activeGame = False
        else:
            self.score = score_candidate

        if self.tetromino.wallOverlap == True:
            self.tetromino_Count = self.tetromino_Count + 1
            tetromino_type = self.tetromino_Index[self.tetromino_Count % 7]
            print("New Tetromino")
            self.tetromino = Tetromino(tetromino_type, False)
            self.ghost_tetromino = Tetromino(tetromino_type, True)
            self.rotation_test_tetromino = Tetromino(tetromino_type, True)
            if (self.tetromino_Count % 7) == 6:
                random.Random().shuffle(self.tetromino_Index)
            #THIS MIGHT BE PART OF THE SOLUTION
            #for brick in self.tetromino.bricks:
            #	for wallBrick in self.tetris_Wall.bricks:
            #		if brick.rect.x == wallBrick.rect.x:
            #			if brick.rect.y + int(screen_height/number_of_rows) >= wallBrick.rect.y :
            #				self.tetromino.wallOverlap = True

        #Redraw, so clear screen, fill background, redraw wall and redraw tetromino
        self.screen.fill(self.screen_bg_colour)

        #Display Score
        msg = "Score: " + str(self.score)
        msg_color = (255, 255, 255)
        f = pygame.font.SysFont(None, 24)
        msg_image = f.render(msg, True, msg_color,None)
        scoresurf = pygame.Surface((20,5), pygame.SRCALPHA, 32)
        scorerect = scoresurf.get_rect()
        scorerect.x = 100
        scorerect.y = 0
        self.screen.blit(msg_image, scorerect)

        #Display Level
        if math.floor(int(time.time()-s) / int(self.level_speed_rate)) > self.level:
            self.level += 1
            self.drop_Tetromino_speed -= self.drop_Tetromino_speed_rate
            pygame.time.set_timer(self.drop_Tetromino, max(self.drop_Tetromino_speed,1))

        level_msg = "Level: " + str(self.level)
        level_msg_color = (255, 255, 0)
        g = pygame.font.SysFont(None, 24)
        level_msg_image = g.render(level_msg, True, level_msg_color,None)
        levelsurf = pygame.Surface((20,5), pygame.SRCALPHA, 32)
        levelrect = levelsurf.get_rect()
        levelrect.x = 0
        levelrect.y = 0
        self.screen.blit(level_msg_image, levelrect)

        #Draw Bricks and Draw Wall
        for brick in self.tetromino.bricks:
        	brick.rect.x = brick.Xcoord
        	brick.rect.y = brick.Ycoord
        	self.screen.blit(brick.surf, brick.rect)
        for brick in self.tetris_Wall.bricks:
            self.screen.blit(brick.surf, brick.rect)

    def updatePausedGame(self):
        oldScore = self.score
        oldLevel = self.level
        oldCount = self.tetromino_Count
        self.screen.fill(self.screen_bg_colour)
        start_msg1 = "TETRIS: (N)ew/(M)achine"
        start_msg1_color = (255, 0, 0)
        start_msg2 = "Tetrominos: " + str(oldCount)
        start_msg2_color = (255, 255, 255)
        start_msg3 = "Level: " + str(oldLevel)
        start_msg3_color = (255, 255, 255)
        start_msg4 = "Score: " + str(oldScore)
        start_msg4_color = (255, 255, 255)
        g = pygame.font.SysFont(None, 22) # - math.ceil(800/screen_height))
        g2 = pygame.font.SysFont(None, 16) # - math.ceil(800/screen_height))
        start_msg1_image = g.render(start_msg1, True, start_msg1_color,None)
        start_msg2_image = g2.render(start_msg2, True, start_msg2_color,None)
        start_msg3_image = g2.render(start_msg3, True, start_msg3_color,None)
        start_msg4_image = g2.render(start_msg4, True, start_msg4_color,None)
        startsurf1 = pygame.Surface((20,5), pygame.SRCALPHA, 32)
        startsurf2 = pygame.Surface((20,5), pygame.SRCALPHA, 32)
        startsurf3 = pygame.Surface((20,5), pygame.SRCALPHA, 32)
        startsurf4 = pygame.Surface((20,5), pygame.SRCALPHA, 32)
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
def play_Tetris():
    tetrisGame = TetrisGame()

    #Main Program Loop
    while True:
        tetrisGame.handleEvents()

        if tetrisGame.paused == False and tetrisGame.activeGame==True:
        	tetrisGame.updateActiveGame(pygame.key.get_pressed())
        elif tetrisGame.activeGame == False:
            tetrisGame.updatePausedGame()

		#Flip to newly drawn screen and increment clock
        pygame.display.flip()
        fpsclock.tick(tetrisGame.FPS)

#Start Game
play_Tetris()
print(time.time()-s)
