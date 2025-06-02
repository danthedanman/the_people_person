import pygame
import sys
import pyperclip

from game import Game

def text_input(screen, clock, prompt, obfuscate_after=None):
    """Display a prompt and capture text input from the user.
    If obfuscate_after is an int, display only the first obfuscate_after characters
    and mask the rest with '*' for security (e.g., API keys)."""
    font = pygame.font.Font(None, 32)
    input_text = ""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                # Handle paste from clipboard (Ctrl+V)
                if (mods & pygame.KMOD_CTRL) and event.key == pygame.K_v:
                    try:
                        clip = pyperclip.paste()
                        input_text += clip
                    except Exception:
                        pass
                elif event.key == pygame.K_RETURN:
                    return input_text
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        screen.fill((30, 30, 30))
        prompt_surf = font.render(prompt, True, (255, 255, 255))
        # Obfuscate display if needed
        if obfuscate_after is not None and len(input_text) > obfuscate_after:
            display_text = input_text[:obfuscate_after] + '*' * (len(input_text) - obfuscate_after)
        else:
            display_text = input_text
        input_surf = font.render(display_text, True, (255, 255, 255))
        screen.blit(prompt_surf, (20, 200))
        screen.blit(input_surf, (20, 240))
        pygame.display.flip()
        clock.tick(30)

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("The People Person")
    clock = pygame.time.Clock()

    # Prompt for API key and player name
    api_key = text_input(screen, clock,
                        "Enter your OpenAI API Key (Ctrl+V to paste):",
                        obfuscate_after=4)
    player_name = text_input(screen, clock, "Enter your gameplay name:")

    # Initialize and run the game
    game = Game(api_key, player_name)
    # Attach screen and clock to game for later use
    game.screen = screen
    game.clock = clock
    game.run()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()