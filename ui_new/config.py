"""
ui_new/config.py

Description:
    * Configuration management for AI Sous Chef

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import json
import os
from pathlib import Path


class Config:
    """Manages app configuration and preferences."""
    
    DEFAULT_CONFIG = {
        'units': 'US',  # 'US' or 'Metric'
        'skill_level': 'Beginner',  # 'Beginner', 'Intermediate', 'Advanced'
        'dietary': [],  # ['vegan', 'gluten-free', etc.]
        'exclusions': [],  # ['peanuts', 'shellfish', etc.]
        'brightness': 80,  # 0-100
    }
    
    def __init__(self):
        self.config_dir = Path.home() / '.ai-sous-chef'
        self.config_file = self.config_dir / 'config.json'
        self.cache_dir = self.config_dir / 'cache'
        
        self._ensure_dirs()
        self.data = self._load()
    
    def _ensure_dirs(self):
        self.config_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults for any missing keys
                    return {**self.DEFAULT_CONFIG, **loaded}
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()
    
    def clear_cache(self):
        """Delete all cached files."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
        return True
    
    def factory_reset(self):
        """Delete all config and cache."""
        import shutil
        if self.config_dir.exists():
            shutil.rmtree(self.config_dir)
        self._ensure_dirs()
        self.data = self.DEFAULT_CONFIG.copy()
        return True
    
    def get_system_info(self):
        """Get system information."""
        import platform
        import sys
        
        info = {
            'App Version': '1.0.0',
            'Python': sys.version.split()[0],
            'Platform': platform.system(),
            'Machine': platform.machine(),
        }
        
        # Pi-specific info
        if platform.system() == 'Linux':
            try:
                with open('/proc/device-tree/model', 'r') as f:
                    info['Device'] = f.read().strip('\x00')
            except:
                pass
        
        return info
    
    def get_network_status(self):
        """Get network connection status."""
        import socket
        
        status = {
            'connected': False,
            'ip': 'Not connected',
            'ssid': 'Unknown',
        }
        
        try:
            # Check internet connectivity
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            status['connected'] = True
            
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            status['ip'] = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Try to get SSID (Linux/Pi only)
        try:
            import subprocess
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            if result.returncode == 0:
                status['ssid'] = result.stdout.strip()
        except:
            pass
        
        return status
    
    def set_brightness(self, value):
        """Set display brightness (Pi only)."""
        import platform
        
        # Save to config regardless of platform
        self.set('brightness', value)
        
        if platform.system() != 'Linux':
            print(f"Brightness set to {value}% (mock - not on Pi)")
            return False
        
        # Try official Raspberry Pi touchscreen backlight
        brightness_paths = [
            '/sys/class/backlight/11-0045/brightness',  # Pi Touch Display 2 (yours)
            '/sys/class/backlight/10-0045/brightness',  # Pi Touch Display 2 (alternate)
            '/sys/class/backlight/rpi_backlight/brightness',
            '/sys/class/backlight/backlight/brightness',
        ]
        
        max_brightness_paths = [
            '/sys/class/backlight/11-0045/max_brightness',
            '/sys/class/backlight/10-0045/max_brightness',
            '/sys/class/backlight/rpi_backlight/max_brightness',
            '/sys/class/backlight/backlight/max_brightness',
        ]
        
        from pathlib import Path
        
        for bright_path, max_path in zip(brightness_paths, max_brightness_paths):
            brightness_file = Path(bright_path)
            max_file = Path(max_path)
            
            if brightness_file.exists():
                try:
                    # Read max brightness
                    if max_file.exists():
                        max_brightness = int(max_file.read_text().strip())
                    else:
                        max_brightness = 255
                    
                    # Calculate actual value (minimum 10% to prevent black screen)
                    min_value = int(max_brightness * 0.1)
                    actual = int(max_brightness * value / 100)
                    actual = max(min_value, actual)
                    
                    # Write brightness
                    brightness_file.write_text(str(actual))
                    print(f"Brightness set to {value}% ({actual}/{max_brightness})")
                    return True
                except PermissionError:
                    try:
                        import subprocess
                        if max_file.exists():
                            max_brightness = int(max_file.read_text().strip())
                        else:
                            max_brightness = 255
                        
                        min_value = int(max_brightness * 0.1)
                        actual = int(max_brightness * value / 100)
                        actual = max(min_value, actual)
                        
                        subprocess.run(
                            ['sudo', 'sh', '-c', f'echo {actual} > {bright_path}'],
                            check=True,
                            timeout=5
                        )
                        print(f"Brightness set to {value}% via sudo")
                        return True
                    except Exception as e:
                        print(f"Brightness sudo error: {e}")
                except Exception as e:
                    print(f"Brightness error for {bright_path}: {e}")
        
        print("No backlight control found")
        return False