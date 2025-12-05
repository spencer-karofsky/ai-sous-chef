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
            return [
                {'ssid': 'HomeNetwork', 'signal': 85, 'secured': True},
                {'ssid': "Spencer's iPhone", 'signal': 70, 'secured': True},
                {'ssid': 'CoffeeShop', 'signal': 45, 'secured': False},
            ]
        
        try:
            # Use nmcli for scanning (more reliable than iwlist)
            result = subprocess.run(
                ['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list', '--rescan', 'yes'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # Fallback to iwlist
                return self._scan_with_iwlist()
            
            return self._parse_nmcli_scan(result.stdout)
        except Exception as e:
            print(f"WiFi scan error: {e}")
            return self._scan_with_iwlist()
    
    def _parse_nmcli_scan(self, output):
        """Parse nmcli scan output."""
        networks = []
        seen = set()
        
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            # nmcli -t format: SSID:SIGNAL:SECURITY
            parts = line.split(':')
            if len(parts) >= 2:
                ssid = parts[0]
                if not ssid or ssid in seen:
                    continue
                
                seen.add(ssid)
                
                try:
                    signal = int(parts[1]) if parts[1] else 0
                except ValueError:
                    signal = 0
                
                # Security field (may be empty for open networks)
                security = parts[2] if len(parts) > 2 else ''
                secured = bool(security and security != '--')
                
                networks.append({
                    'ssid': ssid,
                    'signal': signal,
                    'secured': secured
                })
        
        return sorted(networks, key=lambda x: x['signal'], reverse=True)
    
    def _scan_with_iwlist(self):
        """Fallback scan using iwlist."""
        try:
            result = subprocess.run(
                ['sudo', 'iwlist', 'wlan0', 'scan'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            return self._parse_iwlist_results(result.stdout)
        except Exception as e:
            print(f"iwlist scan error: {e}")
            return []
    
    def _parse_iwlist_results(self, output):
        """Parse iwlist scan output."""
        networks = []
        current = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if 'Cell' in line and 'Address' in line:
                if current.get('ssid'):
                    networks.append(current)
                current = {'ssid': '', 'signal': 0, 'secured': False}
            
            elif 'ESSID:' in line:
                match = re.search(r'ESSID:"(.+)"', line)
                if match:
                    current['ssid'] = match.group(1)
            
            elif 'Signal level' in line:
                match = re.search(r'Signal level[=:](-?\d+)', line)
                if match:
                    dbm = int(match.group(1))
                    if dbm <= -100:
                        current['signal'] = 0
                    elif dbm >= -50:
                        current['signal'] = 100
                    else:
                        current['signal'] = 2 * (dbm + 100)
            
            elif 'Encryption key:on' in line:
                current['secured'] = True
        
        if current.get('ssid'):
            networks.append(current)
        
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
            return True, "Connected (mock)"
        
        try:
            # First, check if we have a saved connection for this SSID
            # If so, try to activate it first
            existing = self._get_connection_name(ssid)
            
            if existing and not password:
                # Try to activate existing connection
                result = subprocess.run(
                    ['sudo', 'nmcli', 'connection', 'up', existing],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return True, "Connected successfully"
            
            # Build the command - pass SSID and password as separate arguments
            # This avoids shell escaping issues
            if password:
                cmd = [
                    'sudo', 'nmcli', 'device', 'wifi', 'connect',
                    ssid,  # nmcli handles special characters when passed as argument
                    'password', password
                ]
            else:
                cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45  # Longer timeout for hotspots
            )
            
            if result.returncode == 0:
                return True, "Connected successfully"
            else:
                error = result.stderr.strip() or result.stdout.strip() or "Connection failed"
                
                # Parse common errors for better messages
                if 'No network with SSID' in error:
                    return False, "Network not found. Make sure hotspot is active."
                elif 'Secrets were required' in error or 'password' in error.lower():
                    return False, "Incorrect password"
                elif 'timeout' in error.lower():
                    return False, "Connection timed out. Try again."
                
                return False, error
                
        except subprocess.TimeoutExpired:
            return False, "Connection timed out. Is the hotspot active?"
        except Exception as e:
            return False, str(e)
    
    def _get_connection_name(self, ssid):
        """Get the nmcli connection name for an SSID (may differ from SSID)."""
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.strip().split('\n'):
                if ':wifi' in line or ':802-11-wireless' in line:
                    name = line.split(':')[0]
                    if name == ssid or ssid in name:
                        return name
        except:
            pass
        return None
    
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
            return None  # Return None for mock so we can test connecting
        
        try:
            # Use nmcli for more reliable results
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'ACTIVE,SSID', 'device', 'wifi'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith('yes:'):
                    return line[4:]  # Everything after 'yes:'
            
            # Fallback to iwgetid
            result = subprocess.run(
                ['iwgetid', '-r'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
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
                ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            networks = []
            for line in result.stdout.strip().split('\n'):
                if ':wifi' in line or ':802-11-wireless' in line:
                    name = line.split(':')[0]
                    if name:
                        networks.append(name)
            return networks
        except:
            return []
    
    def forget_network(self, ssid):
        """Remove a saved network."""
        if not self.is_pi:
            return True
        
        try:
            # Find the connection name (might be different from SSID)
            conn_name = self._get_connection_name(ssid) or ssid
            
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', conn_name],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False