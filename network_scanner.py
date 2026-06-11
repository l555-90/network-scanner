

import socket
import subprocess
import ipaddress
import concurrent.futures
from typing import List, Tuple

def get_local_ip() -> str:
    """Get the local IP address"""
    try:
        # Create a socket and connect to an external address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def get_network_range(ip: str) -> str:
    """Convert IP to network range (assumes /24 subnet)"""
    ip_parts = ip.split('.')
    return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"

def ping_host(ip: str) -> Tuple[str, bool, str]:
    """Ping a single host and try to resolve hostname"""
    try:
        # Try to ping with timeout
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '1', str(ip)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2
        )
        
        is_alive = result.returncode == 0
        hostname = "Unknown"
        
        if is_alive:
            try:
                hostname = socket.gethostbyaddr(str(ip))[0]
            except:
                hostname = "Unknown"
        
        return (str(ip), is_alive, hostname)
    except:
        return (str(ip), False, "Unknown")

def scan_network(network_range: str, max_workers: int = 50) -> List[Tuple[str, str]]:
    """Scan the network for active hosts"""
    print(f"Scanning network: {network_range}")
    print("This may take a minute...\n")
    
    network = ipaddress.IPv4Network(network_range, strict=False)
    active_hosts = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(ping_host, str(ip)): ip for ip in network.hosts()}
        
        completed = 0
        total = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 10 == 0:
                print(f"Progress: {completed}/{total} hosts checked...", end='\r')
            
            ip, is_alive, hostname = future.result()
            if is_alive:
                active_hosts.append((ip, hostname))
    
    print(f"\nScan complete! Found {len(active_hosts)} active devices.\n")
    return sorted(active_hosts, key=lambda x: ipaddress.IPv4Address(x[0]))

def main():
    print("=" * 60)
    print("NETWORK SCANNER - Find devices on your local network")
    print("=" * 60)
    print()
    
    # Get local IP and network range
    local_ip = get_local_ip()
    network_range = get_network_range(local_ip)
    
    print(f"Your IP address: {local_ip}")
    print(f"Network range: {network_range}")
    print()
    
    # Scan the network
    active_hosts = scan_network(network_range)
    
    # Display results
    if active_hosts:
        print("ACTIVE DEVICES FOUND:")
        print("-" * 60)
        print(f"{'IP Address':<20} {'Hostname'}")
        print("-" * 60)
        
        for ip, hostname in active_hosts:
            marker = " (YOU)" if ip == local_ip else ""
            print(f"{ip:<20} {hostname}{marker}")
        
        print("-" * 60)
        print(f"\nTotal devices found: {len(active_hosts)}")
    else:
        print("No active devices found on the network.")
    
    print()

if __name__ == "__main__":
    main()
