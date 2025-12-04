"""
ui/home_screen.py

Description:
    * Home screen / wallpaper for AI Sous Chef
    * Displayed when no recipe is active

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
import math

# Colors - Sleek Blue theme
BLUE_DARK = (13, 27, 42)
BLUE_MID = (27, 38, 59)
BLUE_LIGHT = (41, 51, 82)
CREAM = (255, 253, 240)
ACCENT = (100, 149, 237)  # Cornflower blue


class HomeScreen:
    """
    Home screen displayed when no recipe is active.
    
    To customize later:
        - Override draw() for custom wallpaper
        - Add animations in update()
        - Load background images in __init__
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.font_large = pygame.font.SysFont("Georgia", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Georgia", 24)
        self.font_small = pygame.font.SysFont("Georgia", 16)
        
        # Animation state (for future use)
        self.ticks = 0
        
        # Optional: Load background image
        # self.background = pygame.image.load("assets/background.png")
        self.background = None
    
    def update(self):
        """Update animation state. Call each frame."""
        self.ticks = pygame.time.get_ticks()
    
    def draw(self, screen: pygame.Surface):
        """
        Draw the home screen.
        
        Override this method to create custom wallpapers.
        """
        # Background
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            self._draw_default_background(screen)
        
        # Content
        self._draw_title(screen)
        self._draw_prompt(screen)
    
    def _draw_default_background(self, screen: pygame.Surface):
        """Default gradient background with subtle pattern."""
        # Vertical gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(13 + (27 - 13) * ratio)
            g = int(27 + (38 - 27) * ratio)
            b = int(42 + (59 - 42) * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (self.width, y))
        
        # Subtle decorative circles (can be made more elaborate later)
        self._draw_decorations(screen)
    
    def _draw_decorations(self, screen: pygame.Surface):
        """Draw subtle decorative elements. Easy to customize."""
        # Pulsing opacity based on time
        pulse = (math.sin(self.ticks / 1000) + 1) / 2  # 0 to 1
        alpha = int(20 + pulse * 15)
        
        # Create transparent surface for decorations
        decor_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Corner accents
        pygame.draw.circle(decor_surface, (*ACCENT[:3], alpha), (-50, -50), 200, 2)
        pygame.draw.circle(decor_surface, (*ACCENT[:3], alpha), (self.width + 50, self.height + 50), 200, 2)
        
        # Center decorative ring
        center_x, center_y = self.width // 2, self.height // 2 - 20
        pygame.draw.circle(decor_surface, (*ACCENT[:3], alpha), (center_x, center_y), 120, 1)
        pygame.draw.circle(decor_surface, (*ACCENT[:3], int(alpha * 0.7)), (center_x, center_y), 140, 1)
        
        screen.blit(decor_surface, (0, 0))
    
    def _draw_title(self, screen: pygame.Surface):
        """Draw the app title."""
        title = self.font_large.render("AI Sous Chef", True, CREAM)
        title_x = self.width // 2 - title.get_width() // 2
        title_y = self.height // 2 - 60
        screen.blit(title, (title_x, title_y))
        
        # Accent underline
        line_width = title.get_width() + 40
        line_x = self.width // 2 - line_width // 2
        pygame.draw.rect(screen, ACCENT, (line_x, title_y + title.get_height() + 5, line_width, 3))
    
    def _draw_prompt(self, screen: pygame.Surface):
        """Draw the tap to start prompt."""
        # Pulsing opacity for prompt
        pulse = (math.sin(self.ticks / 500) + 1) / 2
        alpha = int(150 + pulse * 105)
        
        prompt = self.font_medium.render("Tap to start cooking", True, (*CREAM[:3], alpha))
        prompt_x = self.width // 2 - prompt.get_width() // 2
        prompt_y = self.height // 2 + 40
        screen.blit(prompt, (prompt_x, prompt_y))
    
    def handle_touch(self, pos: tuple) -> bool:
        """
        Handle touch input.
        
        Returns:
            True if should transition to search view
        """
        # Any tap transitions to search
        return True


# For future expansion: Alternative home screen styles

class MinimalHomeScreen(HomeScreen):
    """Minimal home screen with just the title."""
    
    def _draw_decorations(self, screen):
        pass  # No decorations


class AnimatedHomeScreen(HomeScreen):
    """Home screen with more elaborate animations."""
    
    def _draw_decorations(self, screen):
        super()._draw_decorations(screen)
        
        # Add floating particles, animated patterns, etc.
        # TODO: Implement when ready for fancier UI
        pass


class ImageHomeScreen(HomeScreen):
    """Home screen with a custom background image."""
    
    def __init__(self, width: int, height: int, image_path: str):
        super().__init__(width, height)
        try:
            self.background = pygame.image.load(image_path)
            self.background = pygame.transform.scale(self.background, (width, height))
        except pygame.error:
            print(f"Could not load background image: {image_path}")
            self.background = None