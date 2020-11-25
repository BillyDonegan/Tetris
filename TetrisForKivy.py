#! /usr/bin/env python
# -*- coding: utf-8 -*-
import kivy
#kivy.require('1.11.1') # replace with your current kivy version !
import time, collections
import numpy as np
import sys
import math
import random
import pygame
from pygame.locals import *
import pynput
from pynput.keyboard import Key, Controller

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
)
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, Line


keyboard = Controller()

#Global Variables - Should Not Change
screen_height = 800
number_of_columns = 10
number_of_rows = 40
screen_width = int(screen_height/4)
tetromino_start_x = int(screen_width/2) - int(screen_width/number_of_columns)
tetromino_start_y = int(screen_height/number_of_rows)

#Timers
#fpsclock = pygame.time.Clock() - NEED TO REPLACE
s=time.time()

#Create Classes:
class tetrisWidget(Widget):
    def __init__(self):
        super(DrawingWidget, self),__init__()

        with self.canvas:
            Color(1,1,1,1)
            self.rect = Rectangle(size=self.size,pos=self.pos)
            self.rect_colour = Colour(1,0,0,1)
            Rectangle(size=(300,100),pos=(300,200))
        self.bind(pos=self.update_rectangle,size=self.update_rectangle)

    def update_rectangle(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size

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

class ML_Game_Screen(AnchorLayout):
    def btn_Left_Press(self):
        self.leftEdge = False
        self.rightEdge = False
        for brick in self.tetromino.bricks:
            if brick.rect.left <= 0:
                self.leftEdge = True
            for wallBrick in self.tetris_Wall.bricks:
                if brick.Xcoord - int(screen_width/number_of_columns) == wallBrick.Xcoord:
                    if brick.Ycoord == wallBrick.Ycoord:
                        self.leftEdge = True
        if self.leftEdge == False and self.tetromino.wallOverlap == False:
            for brick in self.tetromino.bricks:
                brick.Xcoord = brick.Xcoord - int(screen_width/number_of_columns)
                brick.rect.x = brick.Xcoord
        pass

    def btn_Right_Press(self):
        self.leftEdge = False
        self.rightEdge = False
        for brick in self.tetromino.bricks:
            if brick.rect.right >= screen_width:
                self.rightEdge = True
            for wallBrick in self.tetris_Wall.bricks:
                if brick.Xcoord + int(screen_width/number_of_columns) == wallBrick.Xcoord:
                    if brick.Ycoord == wallBrick.Ycoord:
                        self.rightEdge = True
        if self.rightEdge == False and self.tetromino.wallOverlap == False:
            for brick in self.tetromino.bricks:
                brick.Xcoord = brick.Xcoord + int(screen_width/number_of_columns)
                brick.rect.x = brick.Xcoord
        pass

    def btn_Rotate_Press(self):
        self.tetromino.rotate()
        pass

    def btn_Drop_Press(self):
        self.tetromino.drop_Tetromino(self.tetris_Wall)
        self.score += 1
        pass

    def btn_Fast_Drop_Press(self): #not working
        print(self.tetromino.wallOverlap)
        for brick in self.tetromino.bricks:
            if brick.Ycoord >  self.number_Of_Rows_With_No_Downkey*int(screen_height/number_of_rows):
                while self.tetromino.wallOverlap == False:
                    self.tetromino.drop_Tetromino(self.tetris_Wall)
                    self.score += 1
        pass

    def btn_Pause_Press(self):
        self.paused = not self.paused
        pass

    def btn_New_Press(self):
        print("New Game!")
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
        pass

    def btn_Quit_Press(self):
        self.activeGame = False
        exit()

    def __init__(self, **kwargs):
        self.i = 0
        kvStringi = StringProperty(0)
        self.drop_Tetromino_speed = 500
        self.drop_Tetromino_speed_rate = 10
        self.level_speed_rate = 45
        self.FPS = 10
        self.screen_Caption = "Tetris"
        self.number_Of_Rows_With_No_Downkey = 3
        self.seed = 1234 #Can be randomised if needed
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
        super(ML_Game_Screen, self).__init__(**kwargs)

    def update(self, dt):
        if self.paused == False and self.activeGame==True:
            self.tetromino.drop_Tetromino(self.tetris_Wall)
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

            #Redraw, so clear screen, fill background, redraw wall and redraw tetromino

            #Display Score

            #Display Level
            if math.floor(int(time.time()-s) / int(self.level_speed_rate)) > self.level:
                self.level += 1
                self.drop_Tetromino_speed -= self.drop_Tetromino_speed_rate
                #pygame.time.set_timer(self.drop_Tetromino, max(self.drop_Tetromino_speed,1))

            #Draw Bricks and Draw Wall
        #elif tetrisGame.activeGame == False:
        #    tetrisGame.updatePausedGame()

        self.kvStringi = str(self.score)
        pass

class ML_GameApp(App):

    def build(self):
        game = ML_Game_Screen()
        #Clock.schedule_interval(self.tetromino.drop_Tetromino, max(self.drop_Tetromino_speed,1))
        Clock.schedule_interval(game.update, 1.0 / 60.0)
        return game


if __name__ == '__main__':
    ML_GameApp().run()

