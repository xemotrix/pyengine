import pygame
from pygame.math import Vector2
from pygame import USEREVENT
from pygame.surfarray import blit_array

from numba import njit 
import numpy as np


from collections import deque
import time

COLOR_SKY = (157, 222, 213)
COLOR_SAND = (0, 0, 0)

AIR = -1
SAND = 0
WATER = 1
ROCK = 2


MAT_COLORS = [
	[(179, 159, 106),(212, 192, 137), (210, 204, 189), (180, 172, 150)],
	[(40, 140, 180), (50, 150, 190), (30, 130, 170), (30, 150, 180)],
	[(50, 50, 50), (60, 60, 60), (40, 40, 40), (100, 50, 50)]
]



SCALE = 8

def scale_down(coords):
	return coords[0]//SCALE, coords[1]//SCALE
def scale_up(coords):
	return coords[0]*SCALE, coords[1]*SCALE

def gen_mat_color(mat_type):
	rand_i = np.random.randint(0,4)
	return MAT_COLORS[mat_type][rand_i]

class pixel:
	def __init__(self, x, y, color, mat_type):
		self.scaling = SCALE
		self.x = x
		self.y = y
		self.color = color
		self.type = mat_type

		# only liquids
		self.liquid_direction_left = np.random.randint(0,2) == 1
	

	@property
	def screen_x(self):
		return self.x*self.scaling


	@property
	def screen_y(self):
		return self.y*self.scaling


	@property
	def shape(self):
		return pygame.Rect(self.screen_x, self.screen_y, self.scaling, self.scaling)

	
	def move(self, d_x, d_y):
		self.x += d_x
		self.y += d_y 


	def set_coords(self, x, y):
		self.x = x
		self.y = y


	def draw(self, screen):
		pygame.draw.rect(screen, self.color, self.shape)


class world:
	def __init__(self, h, w):
		self.h = h
		self.w = w
		
		self.pixels = {}
		self.update_q = deque([])
		self.lclick_down = False
		self.rclick_down = False
		self.mclick_down = False

		self.materials = set()


	def draw(self, screen):
		while self.update_q:
			x, y = self.update_q.pop()
			self.pixels[x, y].draw(screen)


	def add_material(self, x, y, mat_type):
		if (x,y) not in self.materials:
			self.materials.add((x, y))
			self.pixels[x, y].color = gen_mat_color(mat_type)
			self.pixels[x, y].type = mat_type
			self.update_q.append((x, y))

		if (x+1,y) not in self.materials and (x-1,y) not in self.materials:
			self.materials.add((x+1, y))
			self.pixels[x+1, y].color = gen_mat_color(mat_type)
			self.pixels[x+1, y].type = mat_type
			self.update_q.append((x+1, y))

			self.materials.add((x-1, y))
			self.pixels[x-1, y].color = gen_mat_color(mat_type)
			self.pixels[x-1, y].type = mat_type
			self.update_q.append((x-1, y))


	def swap_pixels(self, p1, p2):
		self.pixels[p1], self.pixels[p2] = self.pixels[p2], self.pixels[p1]
		self.pixels[p1].x, self.pixels[p2].x = self.pixels[p2].x, self.pixels[p1].x
		self.pixels[p1].y, self.pixels[p2].y = self.pixels[p2].y, self.pixels[p1].y

		self.update_q.append(p1)
		self.update_q.append(p2)


	def move_material(self, p1, p2):
		self.swap_pixels(p1, p2)
		self.materials.remove(p1)
		self.materials.add(p2)


	def swap_material(self, p1, p2):
		self.swap_pixels(p1, p2)


	def destroy_material(self, p):
		if p in self.materials:
			self.pixels[p].type = -1
			self.pixels[p].color = COLOR_SKY
			self.update_q.append(p)
			self.materials.remove(p)

		x, y = p
		p_left = x-1,y
		p_right = x+1,y
		if (x+1,y) in self.materials and (x-1,y) in self.materials:
			self.pixels[p_left].type = -1
			self.pixels[p_left].color = COLOR_SKY
			self.update_q.append(p_left)
			self.materials.remove(p_left)

			self.pixels[p_right].type = -1
			self.pixels[p_right].color = COLOR_SKY
			self.update_q.append(p_right)
			self.materials.remove(p_right)


	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN:
			x, y = scale_down(event.pos)

			if event.button == 1:
				self.lclick_down = True
			

			elif event.button == 2:
				self.mclick_down = True

				#click = scale_down(event.pos)
				#print(click, click in self.materials, click in self.pixels )
				#if click in self.pixels:
				#	print(self.pixels[click].type, self.pixels[click].color)
				

			elif event.button == 3:
				self.rclick_down = True
				
		
		elif event.type == pygame.MOUSEBUTTONUP: 
			if event.button == 1:
				self.lclick_down = False
			elif event.button == 2:
				self.mclick_down = False
			elif event.button == 3:
				self.rclick_down = False


	def update(self):
		if self.lclick_down:
			x, y = scale_down(event.pos)
			self.add_material(x, y, SAND)
		elif self.rclick_down:
			x, y = scale_down(event.pos)
			self.add_material(x, y, WATER)
		elif self.mclick_down:
			x, y = scale_down(event.pos)
			#self.destroy_material((x,y))
			self.add_material(x, y, ROCK)
		
		for x, y in list(self.materials):
			mat_type = self.pixels[x, y].type

			if mat_type == SAND:
				# colide with bottom of screen
				if y == self.h-1:
					pass
				# if a material pixel exists below
				elif (x, y+1) in self.materials:

					if self.pixels[x, y+1].type == WATER:
						self.swap_material((x,y), (x, y+1))

					else:

					
						if x >= 1 and (x-1, y+1) not in self.materials:
							self.move_material((x,y), (x-1, y+1))
						elif x >= 1 and self.pixels[x-1, y+1].type == WATER:
							self.swap_material((x,y), (x-1, y+1))
							

						elif x <= self.w-2 and (x+1, y+1) not in self.materials:
							self.move_material((x,y), (x+1, y+1))
						elif x <= self.w-2 and self.pixels[x+1, y+1].type == WATER:
							self.swap_material((x,y), (x+1, y+1))


							

				else:
					self.move_material((x,y), (x, y+1))
					

			elif mat_type == WATER:
				# colide with bottom of screen
				if y == self.h-1:
					pass
				# if a water pixel exists below
				elif (x, y+1) in self.materials:
					
					
					# move down left
					if (x >= 1) and ((x-1, y+1) not in self.materials):
						self.move_material((x,y), (x-1, y+1))
					# move down right
					elif (x <= self.w-2) and ((x+1, y+1) not in self.materials):
						self.move_material((x,y), (x+1, y+1))
					
					# move horizontal	
					elif (x+1, y+1) in self.materials and (x-1, y+1) in self.materials:


						# move horizontal left
						if self.pixels[x, y].liquid_direction_left:
							if (x < 1) or (x-1, y) in self.materials:
								self.pixels[x, y].liquid_direction_left = False
							else:
								self.move_material((x,y), (x-1, y))

						# move horizontal right
						else:
							if (x > self.w-2) or (x+1, y) in self.materials:
								self.pixels[x, y].liquid_direction_left = True
							else:
								self.move_material((x,y), (x+1, y))
						

					# spawn water

					chance_to_spawn = np.random.randint(0,100)
					if chance_to_spawn == 0:
						#print('--',chance_to_spawn)
						if x >= 1 and (x-1, y+1) in self.materials and (x-1, y) not in self.materials:
							#print(chance_to_spawn)
							self.pixels[x-1, y].type = WATER
							self.pixels[x-1, y].color = MAT_COLORS[WATER][0]
							self.materials.add((x-1, y))
							self.update_q.append((x-1, y))

						elif x <= self.w-2 and (x+1, y+1) in self.materials and (x+1, y) not in self.materials:
							self.pixels[x+1, y].type = WATER
							self.pixels[x+1, y].color = MAT_COLORS[WATER][0]
							self.materials.add((x+1, y))
							self.update_q.append((x+1, y))	
				else:
					self.move_material((x,y), (x, y+1))
			

			elif mat_type == ROCK:
				pass


if __name__ == '__main__':

	pygame.init()
	clock = pygame.time.Clock()
	infoObject = pygame.display.Info()
	current_w, current_h = infoObject.current_w, infoObject.current_h
	screen = pygame.display.set_mode((current_w,current_h), pygame.FULLSCREEN)
	

	world_w, world_h = int(current_w/SCALE), int(current_h/SCALE)

	wo = world(world_h, world_w)

	for y in range(world_h):
		for x in range(world_w):
			wo.pixels[(x,y)] = pixel(x, y, COLOR_SKY, -1)
			wo.update_q.append((x,y))

	running = True
	while running:
		##### Handle events ###################################################
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			else:
				wo.handle_event(event)

		wo.update()
		wo.draw(screen)

		clock.tick(40)
		#print('fps', str(int(clock.get_fps())))
		pygame.display.update()
		
		
