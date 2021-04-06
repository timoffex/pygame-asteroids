"""This module keeps track of all user input information on every frame.

This module is responsible for calling `pygame.event.get()` and no other code
should touch the pygame.event or the pygame.key functions.

"""
import pygame


_did_quit = False


def did_quit():
    """Returns whether the application received the QUIT signal."""
    return _did_quit


def is_key_down(key_code):
    """Returns whether the specified key is currently pressed.

    The key_code should be one of the `pygame.K_` constants, such as
    pygame.K_a (the A key) or pygame.K_SPACE (the space bar).

    """
    return pygame.key.get_pressed()[key_code]


def start_new_frame():
    """Processes events at the start of a new frame.

    Call this before doing any extra processing for the frame.

    """
    global _did_quit

    for event in pygame.event.get():
        if event.type is pygame.QUIT:
            _did_quit = True
