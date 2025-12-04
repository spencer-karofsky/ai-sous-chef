"""
ui_new/wifi_manager.py

Description:
    * WiFi management for Raspberry Pi

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import subprocess
import re
import platform


class WiFiManager:
    """Manages WiFi connections on Raspberry Pi."""
    
    def __init__(self):
        self.is_pi = platform.system() == 'Linux'
    
    def scan_networks(self):
        """Scan for available WiFi networks."""
        if not self.is_pi:
            # Return mock data for testing on Mac
            return [
                {'ssid': 'HomeNetwork', 'signal': 85, 'secured': True},
                {'ssid': 'Neighbor_WiFi', 'signal': 60, 'secured': True},
                {'ssid': 'CoffeeShop', 'signal': 45, 'secured': False},
            ]
        
        try:
            # Scan for networks
            result = subprocess.run(
                ['sudo', 'iwlist', 'wlan0', 'scan'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            return self._parse_scan_results(result.stdout)
        except Exception as e:
            print(f"WiFi scan error: {e}")
            return []
    
    def _parse_scan_results(self, output):
        """Parse iwlist scan output."""
        networks = []
        current = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            # New cell/network
            if 'Cell' in line and 'Address' in line:
                if current.get('ssid'):
                    networks.append(current)
                current = {'ssid': '', 'signal': 0, 'secured': False}
            
            # SSID
            elif 'ESSID:' in line:
                match = re.search(r'ESSID:"(.+)"', line)
                if match:
                    current['ssid'] = match.group(1)
            
            # Signal strength
            elif 'Signal level' in line:
                match = re.search(r'Signal level[=:](-?\d+)', line)
                if match:
                    # Convert dBm to percentage (roughly)
                    dbm = int(match.group(1))
                    if dbm <= -100:
                        current['signal'] = 0
                    elif dbm >= -50:
                        current['signal'] = 100
                    else:
                        current['signal'] = 2 * (dbm + 100)
            
            # Encryption
            elif 'Encryption key:on' in line:
                current['secured'] = True
        
        # Don't forget last network
        if current.get('ssid'):
            networks.append(current)
        
        # Remove duplicates and sort by signal
        seen = set()
        unique = []
        for n in networks:
            if n['ssid'] and n['ssid'] not in seen:
                seen.add(n['ssid'])
                unique.append(n)
        
        return sorted(unique, key=lambda x: x['signal'], reverse=True)
    
    def connect(self, ssid, password=None):
        """Connect to a WiFi network."""
        if not self.is_pi:
            # Mock success for testing
            return True, "Connected (mock)"
        
        try:
            # Use nmcli for connection (NetworkManager)
            if password:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            if result.returncode == 0:
                return True, "Connected successfully"
            else:
                error = result.stderr.strip() or "Connection failed"
                return False, error
                
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            return False, str(e)
    
    def disconnect(self):
        """Disconnect from current WiFi."""
        if not self.is_pi:
            return True
        
        try:
            subprocess.run(
                ['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'],
                capture_output=True,
                timeout=10
            )
            return True
        except:
            return False
    
    def get_current_network(self):
        """Get currently connected network name."""
        if not self.is_pi:
            return "MockNetwork"
        
        try:
            result = subprocess.run(
                ['iwgetid', '-r'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def get_saved_networks(self):
        """Get list of saved/known networks."""
        if not self.is_pi:
            return ['HomeNetwork', 'WorkWiFi']
        
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'show'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            networks = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 3 and 'wifi' in line.lower():
                    # First part is name (may have spaces, so join until UUID)
                    networks.append(parts[0])
            return networks
        except:
            return []
    
    def forget_network(self, ssid):
        """Remove a saved network."""
        if not self.is_pi:
            return True
        
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', ssid],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False