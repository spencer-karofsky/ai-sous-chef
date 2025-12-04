"""
ui_new/views/create_view.py

Description:
    * Create view - AI recipe generation

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import pygame
from ui_new.constants import *


class CreateView:
    def __init__(self, fonts):
        self.fonts = fonts
    
    def draw(self, screen, state, keyboard_visible):
        content_bottom = HEIGHT - NAV_HEIGHT
        if keyboard_visible:
            content_bottom = HEIGHT - KEYBOARD_HEIGHT
        
        self._draw_header(screen)
        self._draw_prompt_area(screen, state)
        self._draw_suggestions(screen, state, content_bottom, keyboard_visible)
    
    def _draw_header(self, screen):
        y = 25
        title = self.fonts['header'].render("Create", True, SOFT_BLACK)
        screen.blit(title, (40, y))
        
        subtitle = self.fonts['small'].render("Generate a recipe with AI", True, DARK_GRAY)
        screen.blit(subtitle, (40, y + 40))
    
    def _draw_prompt_area(self, screen, state):
        y = 110
        
        area_rect = pygame.Rect(40, y, WIDTH - 80, 120)
        pygame.draw.rect(screen, LIGHT_GRAY, area_rect, border_radius=16)
        
        text_x = area_rect.x + 25
        text_y = area_rect.y + 20
        
        if state['create_text']:
            words = state['create_text'].split()
            lines = []
            current_line = ""
            max_width = area_rect.width - 50
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if self.fonts['body'].size(test_line)[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for i, line in enumerate(lines[:3]):
                text = self.fonts['body'].render(line, True, SOFT_BLACK)
                screen.blit(text, (text_x, text_y + i * 32))
            
            if state['active_input'] == 'create' and pygame.time.get_ticks() % 1000 < 500:
                last_line = lines[-1] if lines else ""
                cursor_x = text_x + self.fonts['body'].size(last_line)[0] + 2
                cursor_y = text_y + (len(lines) - 1) * 32
                pygame.draw.rect(screen, SOFT_BLACK, (cursor_x, cursor_y, 2, 28))
        else:
            placeholder = self.fonts['body'].render("Describe what you'd like to cook...", True, MID_GRAY)
            screen.blit(placeholder, (text_x, text_y))
            
            hint = self.fonts['small'].render("e.g., 'healthy chicken dinner under 500 calories'", True, MID_GRAY)
            screen.blit(hint, (text_x, text_y + 40))
        
        btn_y = y + 140
        btn_rect = pygame.Rect(40, btn_y, WIDTH - 80, 56)
        
        if state['create_text']:
            pygame.draw.rect(screen, SOFT_BLACK, btn_rect, border_radius=12)
            btn_text = self.fonts['body'].render("Generate Recipe", True, WHITE)
        else:
            pygame.draw.rect(screen, LIGHT_GRAY, btn_rect, border_radius=12)
            btn_text = self.fonts['body'].render("Generate Recipe", True, MID_GRAY)
        
        screen.blit(btn_text, (btn_rect.x + btn_rect.width // 2 - btn_text.get_width() // 2, btn_rect.y + 14))
        
        if state.get('create_status'):
            status = self.fonts['caption'].render(state['create_status'], True, DARK_GRAY)
            screen.blit(status, (40, btn_y + 65))
    
    def _draw_suggestions(self, screen, state, content_bottom, keyboard_visible):
        if keyboard_visible:
            return
        
        y = 340
        
        section_title = self.fonts['small'].render("Quick ideas", True, DARK_GRAY)
        screen.blit(section_title, (40, y))
        
        suggestions = [
            "Quick weeknight pasta",
            "Healthy breakfast bowl",
            "Comfort food dinner",
            "30-minute meal",
        ]
        
        chip_x = 40
        chip_y = y + 35
        
        for suggestion in suggestions:
            chip_width = self.fonts['small'].size(suggestion)[0] + 30
            
            if chip_x + chip_width > WIDTH - 40:
                chip_x = 40
                chip_y += 50
            
            if chip_y + 40 > content_bottom:
                break
            
            chip_rect = pygame.Rect(chip_x, chip_y, chip_width, 40)
            pygame.draw.rect(screen, WHITE, chip_rect, border_radius=20)
            pygame.draw.rect(screen, DIVIDER, chip_rect, 1, border_radius=20)
            
            chip_text = self.fonts['small'].render(suggestion, True, CHARCOAL)
            screen.blit(chip_text, (chip_x + 15, chip_y + 10))
            
            chip_x += chip_width + 12
    
    def handle_touch(self, pos, state, keyboard_visible):
        x, y = pos
        
        if 40 <= x <= WIDTH - 40 and 110 <= y <= 230:
            return 'focus_create'
        
        if 40 <= x <= WIDTH - 40 and 250 <= y <= 306:
            if state['create_text']:
                return 'generate'
        
        if not keyboard_visible:
            suggestions = [
                "Quick weeknight pasta",
                "Healthy breakfast bowl",
                "Comfort food dinner",
                "30-minute meal",
            ]
            
            chip_x = 40
            chip_y = 375
            
            for suggestion in suggestions:
                chip_width = self.fonts['small'].size(suggestion)[0] + 30
                
                if chip_x + chip_width > WIDTH - 40:
                    chip_x = 40
                    chip_y += 50
                
                chip_rect = pygame.Rect(chip_x, chip_y, chip_width, 40)
                if chip_rect.collidepoint(pos):
                    return f'suggestion_{suggestion}'
                
                chip_x += chip_width + 12
        
        return None