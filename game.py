# import dependencies
import pygame
import random 
import neat         
import time
import os
pygame.font.init()


# Load images and set window dimensions
WINDOW_WID = 550
WINDOW_HEIGHT = 800
WINDOW = pygame.display.set_mode((WINDOW_WID, WINDOW_HEIGHT))
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
FONT1 = pygame.font.SysFont("helvetica", 50)


class Bird:
    IMS = BIRD_IMAGES
    MAX_ROT = 25
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.height = self.y
        self.tilt = 0
        self.vel = 0
        self.img_count = 0
        self.img_ind = self.IMS[0]
        self.time = 0  # more like a tick count but it makes it easier to visualize the displacement formula used later

    
    def jump(self):
        # Jumping up 
        self.vel = -10.5
        self.time = 0
        self.height -= self.y

    def move(self):
        # accounts for displacement and tilt

        self.time += 1

        disp = self.vel * self.time + 0.5*3*(self.time**2)
        
        # as we're going up increase disp. Subtracting because velocity is negative
        if disp < 0:
            disp -= 3

        # account for terminal velocity
        if disp > 12: 
            disp = 12
        
        self.y += disp

        # tilt up if moving up 
        if disp < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROT:
                self.tilt = self.MAX_ROT
        
        # tilt down otherwise
        else: 
            if self.tilt < -90:
                self.tilt -= 20 # tilt down slowly so it doesn't look like we are just changing pictures. 
    
    def animate(self, window): 
        # Changes animation according to frame
        self.img_count += 1 # increase img_count. Will use this for animations


        if self.img_count % 100 < 10: 
            self.img = self.IMS[0]
        elif self.img_count % 100 < 20: 
            self.img = self.IMS[1]
        elif self.img_count % 100 < 30:
            self.img = self.IMS[2]
        elif self.img_count % 100 < 40:
            self.img = self.IMS[0]
        elif self.img_count % 100 < 50:
            self.img = self.IMS[0]
            self.img_count = 0
        
        # If at a certain angle or nosediving, don't animate

        if self.tilt < -80:
            self.img = self.IMS[1]
            self.img_count = 20

        # rotates around center and not according to the top left pixel of the image
        # got it from this link: https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
        rotated = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated.get_rect(center = self.img.get_rect(topleft=(self.x, self.y)).center)
        window.blit(rotated, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img_ind)

        # Had to search this one up too :) link: https://stackoverflow.com/questions/48025283/pixel-perfect-collision-detection-for-sprites-with-a-transparent-background

class Pipe:
    VEL = 5 # The bird doesn't have a horizontal speed. Instead, the ground and the pipes move to give the illusion that the bird is moving.
    GAP = 250 # Gap between pipes. 

    def __init__(self, x):
        self.x = x
        self.height = 0
        
        self.top = 0
        self.bottom = 0

        self.TOP_PIPE = pygame.transform.flip(PIPE_IMG, False, True)    # Flip the image using pygame because I didn't want to do it using other software LOL
        self.BOTTOM_PIPE = PIPE_IMG
        self.passed = False

        self.generatePipes()

    def generatePipes(self):
        # Generate the pipes at a random height
        self.height = random.randrange(40, 450)
        self.top = self.height - self.TOP_PIPE.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def show(self, window): # draw the actual images on the display
        window.blit(self.TOP_PIPE, (self.x, self.top))
        window.blit(self.BOTTOM_PIPE, (self.x, self.bottom))
    

    def collide(self, bird):
        # Check for collision with the bird
        bird_mask = bird.get_mask()
        t_mask = pygame.mask.from_surface(self.TOP_PIPE)
        b_mask = pygame.mask.from_surface(self.BOTTOM_PIPE)

        t_offset = (self.x - bird.x, self.top - round(bird.y))
        b_offset = (self.x - bird.x, self.bottom - round(bird.y))

        t_poc = bird_mask.overlap(t_mask, t_offset)
        b_poc = bird_mask.overlap(b_mask, b_offset)

        if t_poc or b_poc:
            return True
        
        return False
    

class Base:
    VEL = 5 # velocity is the same as the pipes or else it would look weird.
    WID = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        
        self.oldx = 0
        self.newx = self.WID

    def move(self):
        self.oldx -= self.VEL   # Move the base to the left

        self.newx -= self.VEL   # Have two pictures of the base rotating between the two

        if self.oldx + self.WID < 0:    # If the first instance of the base passes the window then replace it with the second picture
            self.oldx = self.newx + self.WID    
        
        if self.newx + self.WID < 0:
            self.newx = self.oldx + self.WID

    
    def show(self, window):
        window.blit(self.IMG, (self.oldx, self.y))
        window.blit(self.IMG, (self.newx, self.y))
        

generation = 0 # Keeps track of which generation is trying out the scenario right now
def draw_all(win, birds, pipes, base, score, generation):

    win.blit(BG, (0, 0)) # Draw the background
    for pipe in pipes: 
        pipe.show(win)

    base.show(win)

    for bird in birds: 
        bird.animate(win)

    sLabel = FONT1.render("Score: " + str(score), 1, (255, 255, 0))
    gLabel = FONT1.render("Generation: " + str(generation), 1, (255,255,0))

    win.blit(sLabel, (WINDOW_WID - sLabel.get_width() - 15, 10))
    win.blit(gLabel, (10, 10))
    pygame.display.update()

def fitness_func(genomes, config):  # Fitness function / Main Game Loop. 
    birds = []
    n_nets = []
    genome = []
    
    global generation 
    generation += 1

    for g_id, ge in genomes:
        ge.fitness = 0 # All birds start with a fitness of 0

        test_net = neat.nn.FeedForwardNetwork.create(ge, config) # Creates a neural network for the specific genome/bird
        n_nets.append(test_net)
        birds.append(Bird(230, 350))
        genome.append(ge)

    base = Base(730)
    pipes = [Pipe(700)]
    points = 0

    clock = pygame.time.Clock()

    running = True
    while running and len(birds) > 0:
        clock.tick(30)  # Capped at 30 FPS

        for event in pygame.event.get():    
            if event.type == pygame.QUIT:   # checks if program has been quit
                running = False
                pygame.quit()
                quit()
                break
                
        pipe_index = 0
        if len(birds) > 0:  # To choose which pipe to feed as input to the Neural Net as at most there can be two pipes on the screen
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].TOP_PIPE.get_width():
                pipe_index = 1
            else:
                pipe_index = 0

        for i, bird in enumerate(birds):   
            genome[i].fitness += 0.1    # Fitness is increased for every frame a bird is alive.
            bird.move()

            output = n_nets[i].activate((bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom))) # sends input to the neural network of a specific bird to get the outputs

            if output[0] > 0.5: # if the output is favourable, jump
                bird.jump()
        base.move()

        removed = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()

            for i, bird in enumerate(birds): 
                if pipe.collide(bird):
                    genome[i].fitness -= 1  # reduce fitness by 1 if the bird collides with the pipe.
                    n_nets.pop(i)
                    genome.pop(i)
                    birds.pop(i)

            if pipe.TOP_PIPE.get_width() + pipe.x < 0:  # If the pipe goes off the screen, then put it into the removed list
                removed.append(pipe)

            if not pipe.passed and bird.x > pipe.x:    # check if bird has passed a pipe
                pipe.passed = True
                add_pipe = True
                
        if add_pipe:
            
            points += 1
            for ge in genome:       # For every pass, add a point, increase fitness by 5, add a new pipe and remove the pipe in the removed list.
                ge.fitness += 5
            pipes.append(Pipe(700)) 
        for pip in removed: 
            pipes.remove(pip)
        
        for i, bird in enumerate(birds):
            if bird.y + bird.img_ind.get_height() - 10 >= 730 or bird.y < 0:    # Check if the bird hit the ground or went off screen.
                birds.pop(i)
                n_nets.pop(i)
                genome.pop(i)
        
        draw_all(WINDOW, birds, pipes, base, points, generation)    # draw all the images onto the window.



def run(config_path):   # Create the population.
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))  # This is for some stats about the calculations going on.
    population.add_reporter(neat.StatisticsReporter())

    final_genome = population.run(fitness_func, 100)    # Run the simulation for 100 generations.


if __name__ == "__main__":
    config_dir = os.path.dirname(__file__)  # Gets current directory

    config_path = os.path.join(config_dir, "config-flappy.txt") # Finds path to the config file
    run(config_path)    # Runs the whole program
            

        
        




    
