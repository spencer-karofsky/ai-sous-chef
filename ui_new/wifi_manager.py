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
                {'ssid': 'HomeNetwork', 'signal': 85, 'secured': True, 'security': 'WPA2'},
                {'ssid': "Spencer's iPhone", 'signal': 70, 'secured': True, 'security': 'WPA2'},
                {'ssid': 'CoffeeShop', 'signal': 45, 'secured': False, 'security': ''},
            ]
        
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list', '--rescan', 'yes'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
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
                
                security = parts[2] if len(parts) > 2 else ''
                secured = bool(security and security != '--')
                
                networks.append({
                    'ssid': ssid,
                    'signal': signal,
                    'secured': secured,
                    'security': security  # Store security type (WPA1, WPA2, WPA3, etc.)
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
                current = {'ssid': '', 'signal': 0, 'secured': False, 'security': ''}
            
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
                current['security'] = 'WPA2'  # Assume WPA2 for iwlist
            
            elif 'WPA2' in line:
                current['security'] = 'WPA2'
            elif 'WPA' in line and 'WPA2' not in current.get('security', ''):
                current['security'] = 'WPA'
        
        if current.get('ssid'):
            networks.append(current)
        
        seen = set()
        unique = []
        for n in networks:
            if n['ssid'] and n['ssid'] not in seen:
                seen.add(n['ssid'])
                unique.append(n)
        
        return sorted(unique, key=lambda x: x['signal'], reverse=True)
    
    def connect(self, ssid, password=None, security_type=None):
        """Connect to a WiFi network."""
        if not self.is_pi:
            return True, "Connected (mock)"
        
        try:
            # First, check if we have a saved connection
            existing = self._get_connection_name(ssid)
            
            if existing:
                # Try to activate existing connection
                result = subprocess.run(
                    ['sudo', 'nmcli', 'connection', 'up', existing],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return True, "Connected successfully"
                
                # If existing connection failed with new password, delete and recreate
                if password:
                    subprocess.run(
                        ['sudo', 'nmcli', 'connection', 'delete', existing],
                        capture_output=True,
                        timeout=10
                    )
            
            # Create new connection with proper security settings
            if password:
                # Determine key management type
                key_mgmt = 'wpa-psk'  # Default to WPA-PSK (covers WPA/WPA2)
                if security_type:
                    if 'WPA3' in security_type:
                        key_mgmt = 'sae'  # WPA3 uses SAE
                    elif 'WPA' in security_type:
                        key_mgmt = 'wpa-psk'
                
                cmd = [
                    'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                    'password', password,
                    'wifi-sec.key-mgmt', key_mgmt
                ]
            else:
                # Open network
                cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45
            )
            
            if result.returncode == 0:
                return True, "Connected successfully"
            else:
                error = result.stderr.strip() or result.stdout.strip() or "Connection failed"
                
                # Parse common errors
                if 'No network with SSID' in error:
                    return False, "Network not found"
                elif 'Secrets were required' in error or 'password' in error.lower():
                    return False, "Incorrect password"
                elif 'timeout' in error.lower():
                    return False, "Connection timed out"
                elif '802-11-wireless-security' in error:
                    # Try alternative security method
                    return self._try_alternative_connect(ssid, password)
                
                return False, error
                
        except subprocess.TimeoutExpired:
            return False, "Connection timed out"
        except Exception as e:
            return False, str(e)
    
    def _try_alternative_connect(self, ssid, password):
        """Try connecting with manual connection profile creation."""
        try:
            # Delete any existing broken connection
            self._delete_connection(ssid)
            
            # Create connection manually with full settings
            # This gives us more control over security settings
            result = subprocess.run([
                'sudo', 'nmcli', 'connection', 'add',
                'type', 'wifi',
                'con-name', ssid,
                'ssid', ssid,
                'wifi-sec.key-mgmt', 'wpa-psk',
                'wifi-sec.psk', password
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                return False, "Failed to create connection profile"
            
            # Now activate it
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'up', ssid],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Connected successfully"
            else:
                error = result.stderr.strip() or "Connection failed"
                if 'Secrets were required' in error:
                    return False, "Incorrect password"
                return False, error
                
        except Exception as e:
            return False, str(e)
    
    def _delete_connection(self, ssid):
        """Delete a connection profile by SSID."""
        try:
            conn_name = self._get_connection_name(ssid) or ssid
            subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', conn_name],
                capture_output=True,
                timeout=10
            )
        except:
            pass
    
    def _get_connection_name(self, ssid):
        """Get the nmcli connection name for an SSID."""
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
            return None
        
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'ACTIVE,SSID', 'device', 'wifi'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith('yes:'):
                    return line[4:]
            
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
            conn_name = self._get_connection_name(ssid) or ssid
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', conn_name],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def is_saved(self, ssid):
        """Check if a network is saved."""
        return ssid in self.get_saved_networks()