## basic implementation of the Chebyshev polynomial and hash function

import hashlib
from sympy import symbols, cos, acos
import time
import random


# Chebyshev polynomial
def chebyshev_polynomial(n, x):
    if n == 0:
        return 1
    elif n == 1:
        return x
    else:
        return 2 * x * chebyshev_polynomial(n - 1, x) - chebyshev_polynomial(n - 2, x)

# Hash function
def hash_function(*args):
    hasher = hashlib.sha256()
    for arg in args:
        hasher.update(str(arg).encode('utf-8'))
    return hasher.hexdigest()


## System Initialization

class GatewayNode:
    def __init__(self):
        self.master_key = None
        self.x = None
        self.phi = None
        self.p = None
        self.sensor_nodes = {}

    def initialize(self):
        # Initialize GWN's master key, x, phi, and prime p
        self.master_key = random.getrandbits(256)  # Random 256-bit number
        self.x = random.uniform(-1, 1)  # x chosen from [-1, 1]
        self.phi = random.randint(1, 10)  # Random number for phi
        self.p = 104729  # Example prime number

        # Compute PG using Chebyshev polynomial
        self.PG = chebyshev_polynomial(self.phi, self.x)

    def register_sensor_node(self, sid):
        # Compute secret key for sensor node
        secret_key = hash_function(sid, self.master_key)
        self.sensor_nodes[sid] = secret_key

    def verify_and_respond(self, did_i, Ei, Li, Ni, T1, sensor_node):
        # Verify freshness of T1
        current_time = time.time()
        if current_time - T1 > 10:  # Assuming 10 seconds as the threshold for freshness
            return None
        
        IDi = did_i ^ chebyshev_polynomial(self.phi, Ei)  # T_phi(Ei)
        fi = hash_function(IDi, self.master_key)
        sid_j = Li ^ hash_function(fi, T1)
        Qi = hash_function(fi, Ei)
        if hash_function(IDi, Qi, sid_j, T1) != Ni:
            return None

        ej = hash_function(sid_j, self.master_key)
        Yi = hash_function(ej, Ei) ^ Qi
        T2 = current_time + 5  # Adding 5 seconds for T2
        Di = hash_function(Qi, Yi, ej, Ei, T2)
        return (Di, Yi, Ei, T2), ej

class SensorNode:
    def __init__(self, sid):
        self.sid = sid
        self.secret_key = None

    def setup(self, secret_key):
        self.secret_key = secret_key

    def verify_and_respond(self, Di, Yi, Ei, T2):
        # Verify T2
        current_time = time.time()
        if current_time - T2 > 10:
            return None
        
        Qi = Yi ^ hash_function(self.secret_key, Ei)
        if hash_function(Qi, Yi, self.secret_key, Ei, T2) != Di:
            return None

        beta = random.randint(1, 10)
        Ri = chebyshev_polynomial(beta, self.x)
        Ki = chebyshev_polynomial(beta, Ei)
        session_key = hash_function(Ki, Qi)
        T3 = current_time + 5
        Gi = hash_function(session_key, Ri)
        Wi = hash_function(Ri, Gi, self.secret_key, Ei, T3)
        return (Ri, Gi, Wi, T3), session_key


## System Initalization script

# Initialize Gateway Node
gwn = GatewayNode()
gwn.initialize()

# Example: Registering a Sensor Node
sensor_node_id = "SN1"
gwn.register_sensor_node(sensor_node_id)

# Initialize Sensor Node
sensor_node = SensorNode(sensor_node_id)
sensor_node.setup(gwn.sensor_nodes[sensor_node_id])

print(f"Sensor Node {sensor_node.sid} initialized with secret key: {sensor_node.secret_key}")

## Define Class for User and Smart Card

class SmartCard:
    def __init__(self):
        self.theta_i = None
        self.Ai = None
        self.Ci = None
        self.gamma = None
        self.PG = None

    def register_user(self, IDi, PWi, Bi, gamma, PG, fi):
        self.gamma = gamma
        self.PG = PG
        # Simulate biometric generation function GEN(Bi)
        sigma_i, self.theta_i = self.GEN(Bi)
        self.Ai = hash_function(IDi, PWi, sigma_i) % gamma
        self.Ci = fi ^ hash_function(PWi, sigma_i)

    def GEN(self, biometric):
        # Simulate biometric generation (this is a placeholder)
        return hash_function(biometric), hash_function(biometric, "theta")
    
    def authenticate_user(self, ID_star_i, PW_star_i, B_star_i, sensor_node_sid):
        sigma_star_i = self.REP(B_star_i, self.theta_i)
        A_star_i = hash_function(ID_star_i, PW_star_i, sigma_star_i) % self.gamma
        
        if A_star_i != self.Ai:
            return None, None
        
        fi = self.Ci ^ hash_function(PW_star_i, sigma_star_i)
        Ei = chebyshev_polynomial(random.randint(1, 10), self.PG)  # T_alpha(x)
        did_i = Ei ^ hash_function(self.IDi)
        Li = sensor_node_sid ^ hash_function(fi, time.time())  # using current timestamp as T1
        Qi = hash_function(fi, Ei)
        Ni = hash_function(self.IDi, Qi, sensor_node_sid, time.time())
        return (did_i, Ei, Li, Ni, time.time()), fi

    def REP(self, biometric_star, theta):
        # Simulated biometric representation (placeholder)
        return hash_function(biometric_star, theta)
    
    def update_password(self, old_password, new_password):
        # Verify old password
        if hash_function(self.IDi, old_password, self.sigma_i) % self.gamma != self.Ai:
            return False  # Old password verification failed

        # Update password
        self.Ci = self.Ci ^ hash_function(old_password, self.sigma_i)  # Revert old Ci
        self.Ci = self.Ci ^ hash_function(new_password, self.sigma_i)  # Apply new Ci
        self.Ai = hash_function(self.IDi, new_password, self.sigma_i) % self.gamma
        return True


class User:
    def __init__(self, IDi):
        self.IDi = IDi
        self.PWi = None
        self.Bi = None
        self.smart_card = SmartCard()

    def register(self, GWN, PWi, Bi):
        self.PWi = PWi
        self.Bi = Bi
        # GWN computes fi
        fi = hash_function(self.IDi, GWN.master_key)
        # Store fi and PG in smart card
        self.smart_card.register_user(self.IDi, self.PWi, self.Bi, 256, GWN.PG, fi)


## User Registration

# User Registration
user_id = "User1"
user_password = "password123"
user_biometric = "biometric_data"

# Create User
user = User(user_id)
user.register(gwn, user_password, user_biometric)

print(f"User {user.IDi} registered with smart card.")

### Authentication and Key Agreement

# Implementing the Authentication Flow

# User tries to authenticate
user_inputs = ("User1", "password123", "biometric_data_star", sensor_node.sid)
auth_request, fi = user.smart_card.authenticate_user(*user_inputs)

if auth_request:
    response_from_gwn, ej = gwn.verify_and_respond(*auth_request, sensor_node)
    if response_from_gwn:
        response_from_sensor_node, session_key = sensor_node.verify_and_respond(*response_from_gwn)
        if response_from_sensor_node:
            print("Authentication successful. Session key established:", session_key)
        else:
            print("Authentication failed at sensor node.")
    else:
        print("Authentication failed at GWN.")
else:
    print("Authentication failed at smart card.")

### Password Update

# User updates their password
old_password = "password123"
new_password = "new_password123"

password_update_success = user.smart_card.update_password(old_password, new_password)
if password_update_success:
    print(f"Password for user {user.IDi} successfully updated.")
else:
    print(f"Failed to update password for user {user.IDi}.")

