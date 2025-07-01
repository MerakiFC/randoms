import os, json, requests
from copy import deepcopy
from dotenv import load_dotenv

load_dotenv()

# Load JSON template
def load_template():
    try:
        # Peer payload template is expected to be in the same directory as this script
        with open('peerPayload.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: peerPayload.json not found")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in peerPayload.json - {e}")
        exit(1)


def integer_to_subnet(integer_value) -> str:
    """
    Convert an integer (0-65535) into a 10.x.y.0/24 subnet.
    
    Args:
        integer_value (int): Integer between 0 and 65535
        
    Returns:
        str: Subnet in format 10.x.y.0/24
        
    Example:
        integer_to_subnet(0) -> "10.0.0.0/24"
        integer_to_subnet(256) -> "10.1.0.0/24"
        integer_to_subnet(513) -> "10.2.1.0/24"
        integer_to_subnet(65535) -> "10.255.255.0/24"
    """
    if not 0 <= integer_value <= 65535:
        raise ValueError("Integer must be between 0 and 65535")
    
    # Split into two 8-bit values using bitwise operations
    second_octet = (integer_value >> 8) & 0xFF  # Upper 8 bits
    third_octet = integer_value & 0xFF          # Lower 8 bits
    
    generated_subnet = f"10.{second_octet}.{third_octet}.0/24"
    #print(f"{integer_value} - {generated_subnet}") #optional, for debugging purposes
    return generated_subnet #f"10.{second_octet}.{third_octet}.0/24"


def create_peer_object(template, count, name, generated_subnet, peerId_start=1000):
    import random
    peer = []
    
    peerId = peerId_start  # Starting peerId
    peer = deepcopy(template['peers'][0]) # Create a deep copy of the template peer from json file

    peer['peerId']  = f'{peerId + count}' # Assign peerId starting from set value
    peer['name'] = f'{name}{count}' # Assign peer name with count value
    
    # Generate random IPs for publicIp, localId, and remoteId
    peer['publicIp'] = f'200.100.{random.randint(0, 255)}.{random.randint(1, 254)}'
    peer['localId'] = f'192.168.{random.randint(0, 255)}.{random.randint(1, 254)}'
    peer['remoteId'] = f'10.0.{random.randint(0, 255)}.{random.randint(1, 254)}'
    
    #Use subnet generator to create privateSubnets, currently only one subnet is used per peer
    peer['privateSubnets'][0] = generated_subnet
    peer['networkTags'][0] = f'peer{count}'
    return peer

def send_vpn_peers(payload):
    
    load_dotenv()
    M_API_KEY=os.getenv('M_API_KEY')
    organizationId=os.getenv('M_ORG_ID')
    #networkId=os.getenv('M_NETWORK_ID')
    
    url = f"https://api.meraki.com/api/v1/organizations/{organizationId}/appliance/vpn/thirdPartyVPNPeers"
    headers = {
        "Authorization": f"Bearer {M_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        #print(f"Request Headers: {response.request.headers}")
        print(f"Content-Length in Request Headers: {response.request.headers.get('Content-Length')} bytes")
        
        if response.status_code in [200, 201]:
            print("✅ VPN peers created successfully!")            
            #print("Response:", response.json())
        else:
            print("❌ Error creating VPN peers:")
            print("Response:", response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test the conversion function

    peer_count = int(input("Number of peers to create: "))
    peer_name = input("Peer name prefix: ")
    template = load_template()
    peers = []
    
    try:
        if not 0 <= peer_count <= 65535:
            raise ValueError("Integer must be between 0 and 65535")
        print(f"Generating {peer_count} peers...")

        for count in range(peer_count):
            peer_index = count + 1  # Start from 1 to avoid 0 subnet
            generated_subnet = integer_to_subnet(peer_index)
            peers.append(create_peer_object(template, count, peer_name, generated_subnet))
        payload = {"peers": peers}
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)    
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    
    #print(json.dumps(peers, indent=2)) #optional, for debugging purposes
    send_vpn_peers(payload)
