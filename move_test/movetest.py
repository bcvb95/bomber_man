import pygame
import time

WIDTH = 700
HEIGHT = 700

STEPSIZE = 1
MINMOVEFREQ = 0.2

class Moveable(object):
    def __init__(self, rect, stepsize, color):
        self.rect = rect
        self.step_size = stepsize
        self.color = color
        self.dest = None
        self.source = self.rect.topleft
        self.last_move = 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    def update(self):
        if self.dest:
            self.movetowarddest()

    def move(self, dir):
        if self.dest:
            return
        self.dest = ((self.rect.topleft[0]+dir[0]*self.rect.width, \
                      self.rect.topleft[1]+dir[1]*self.rect.height))
        self.source = self.rect.topleft

    def movetowarddest(self):
        pos = self.rect.topleft
        if abs(self.dest[0] - pos[0]) + abs(self.dest[1] - pos[1]) <= self.step_size:
            self.rect.topleft = self.dest
            self.dest = None
            self.last_move = time.time()
            return
        if self.dest[0] > pos[0]:
            self.move_step((1, 0))
        elif self.dest[0] < pos[0]:
            self.move_step((-1, 0))
        elif self.dest[1] > pos[1]:
            self.move_step((0, 1))
        elif self.dest[1] < pos[1]:
            self.move_step((0, -1))

    def move_step(self, dir):
        self.rect.topleft = (self.rect.topleft[0]+dir[0]*self.step_size, \
                             self.rect.topleft[1]+dir[1]*self.step_size)

direction_input_dict = {
    pygame.K_LEFT:  (-1, 0),
    pygame.K_a:     (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_d:     (1, 0),
    pygame.K_UP:    (0, -1),
    pygame.K_w:     (0, -1),
    pygame.K_DOWN:  (0, 1),
    pygame.K_s:     (0, 1)
}

def main():
    pygame.init()
    pygame.display.set_caption("move test")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    moveable1 = Moveable(pygame.Rect((WIDTH/2, HEIGHT/2), (50, 50)), stepsize=STEPSIZE, color=(245, 25, 10))
    bombs = []
    running = True
    queued_dir_input = (0,0)
    dir_input = (0,0)
    while running:
        do_move = time.time() - moveable1.last_move > MINMOVEFREQ
        for event in pygame.event.get():
            if event.type == pygame.QUIT \
            or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key in direction_input_dict:
                    dir_input = direction_input_dict[event.key]
                elif event.key == pygame.K_SPACE:
                    if not moveable1.dest:
                        bombs.append(pygame.Rect(moveable1.rect.topleft, moveable1.rect.size))
                    else:
                        bombs.append(pygame.Rect(moveable1.source, moveable1.rect.size))
            elif event.type == pygame.KEYUP:
                if event.key in direction_input_dict:
                    if not do_move:
                        queued_dir_input = dir_input
                    dir_input = (0, 0)
        if do_move:
            if queued_dir_input != (0,0):
                moveable1.move(queued_dir_input)
                queued_dir_input = (0,0)
            else:
                moveable1.move(dir_input)

        # update
        moveable1.update()

        # draw
        screen.fill((255, 255, 255))

        for bomb in bombs:
            pygame.draw.rect(screen, (0,0,0), bomb)
        moveable1.draw(screen)

        pygame.display.flip()

if __name__ == "__main__":
    main()