#%%

import pygame
import random

random.seed(44)

settings_file = "settings.txt"
channels_file = "channels.txt"
diagonal_select_channel = None
n = 4
selected_channels = set()  # Track selected cells on the diagonal

# Read combinations (nodes.txt)
with open(channels_file, "r") as file:
    combinations = [line.strip() for line in file.readlines()]

# Read selected channels and convert coordinates to lists
with open(settings_file, "r") as file:
    selected_channels = []
    lines = file.readlines()
    for line in lines[5:]:  # Skip header
        if line.strip():
            selected_channels.append(list(map(int, line.strip().split(","))))
                
# Load and initialize Pygame
pygame.init()
screen = pygame.display.set_mode((900, 800))
pygame.display.set_caption("Channel Distribution Table")

# Define colors
black = (0, 0, 0)
white = (255, 255, 255)
background_color = (30, 30, 30)
grid_color = (200, 200, 200)
signal_color = (255, 100, 100)   # Color for signal photon channels
idler_color = (100, 100, 255)    # Color for idler photon channels
legend_color = (200, 200, 200)
font = pygame.font.SysFont(None, 48)

# Define the channels as before
channels = [f"C{i}" if j % 2 == 0 else f"H{i}" for i in range(14, 38) for j in range(2)]

# Distribution of channels to nodes
node_distributions = {}
node_distributions_number = {}
node_distributions_type = {}

# Function to attempt assignment and check for duplicates
def assign_channels(combinations, selected_channels):
    channels = [f"C{i}" if j % 2 == 0 else f"H{i}" for i in range(14, 38) for j in range(2)]
    
    # The sets containing the assigned channels to the nodes 
    node_distributions = {}
    node_distributions_number = {}
    node_distributions_type = {}

    # Assign channels based on combinations and selected channels
    for idx, comb in enumerate(combinations):
        if idx < len(selected_channels):
            node1, node2 = comb[0], comb[1]
            ch1_idx, ch2_idx = selected_channels[idx]
            ch1, ch2 = channels[ch1_idx], channels[ch2_idx]

            # Initialize nodes if they don't exist in distributions
            for node in (node1, node2):
                if node not in node_distributions:
                    node_distributions[node] = []
                    node_distributions_number[node] = []
                    node_distributions_type[node] = []

            # Ensure each node has unique channels by avoiding duplicates
            if ch1 not in node_distributions[node1] and ch2 not in node_distributions[node2]:
                # Normal assignment
                node_distributions[node1].append(ch1)
                node_distributions_number[node1].append(ch1_idx)
                node_distributions_type[node1].append("s")

                node_distributions[node2].append(ch2)
                node_distributions_number[node2].append(ch2_idx)
                node_distributions_type[node2].append("i")
            else:
                # Swap assignment if a conflict is found
                if ch1 in node_distributions[node1]:
                    node_distributions[node1].append(ch2)
                    node_distributions_number[node1].append(ch2_idx)
                    node_distributions_type[node1].append("i")

                    node_distributions[node2].append(ch1)
                    node_distributions_number[node2].append(ch1_idx)
                    node_distributions_type[node2].append("s")
                else:
                    node_distributions[node1].append(ch1)
                    node_distributions_number[node1].append(ch1_idx)
                    node_distributions_type[node1].append("s")

                    node_distributions[node2].append(ch2)
                    node_distributions_number[node2].append(ch2_idx)
                    node_distributions_type[node2].append("i")

    # Check for duplicates
    for node, channels in node_distributions.items():
        if len(set(channels)) != len(channels):
            # Duplicate found
            return False, node_distributions, node_distributions_number, node_distributions_type

    # No duplicates found
    return True, node_distributions, node_distributions_number, node_distributions_type


# Main loop to attempt shuffling and assignment
max_attempts = 20
attempt = 0
success = False
while attempt < max_attempts and not success:
    success, node_distributions, node_distributions_number, node_distributions_type \
        = assign_channels(combinations, selected_channels)
    
    if not success:
        print(f"Duplicate detected in attempt {attempt + 1}. Shuffling combinations and channels.")
        # Shuffle combinations and selected channels in sync
        paired_data = list(zip(combinations, selected_channels))
        random.shuffle(paired_data)
        combinations, selected_channels = zip(*paired_data)
        attempt += 1

if success:
    print("Assignment successful with no duplicates.")
else:
    print("Failed to resolve duplicates after maximum attempts.")
        
# Create new dictionaries to store the sorted results
sorted_node_distributions = {}
sorted_node_distributions_number = {}
sorted_node_distributions_type = {}

# Sorting function
for node in sorted(node_distributions.keys()):  # Ensuring alphabetical order of nodes
    # Combine channel, number, and type information into tuples for sorting
    combined = list(zip(
        node_distributions[node],
        node_distributions_number[node],
        node_distributions_type[node]
    ))
    
    # Sort by type ('s' comes before 'i') and by number within each type
    combined.sort(key=lambda x: (x[2] != 's', x[1]))
    
    # Unzip the sorted tuples back into the new dictionaries
    sorted_node_distributions[node], sorted_node_distributions_number[node], sorted_node_distributions_type[node] = zip(*combined)

    # Convert back to lists if needed
    sorted_node_distributions[node] = list(sorted_node_distributions[node])
    sorted_node_distributions_number[node] = list(sorted_node_distributions_number[node])
    sorted_node_distributions_type[node] = list(sorted_node_distributions_type[node])

# Pygame display for the distribution table
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill(black)
    
    # Display distribution table
    y_offset = 20
    for node, assigned_channels in sorted_node_distributions.items():
        # Render node and assigned channels
        node_label = font.render(f"Node {node}:", True, legend_color)
        screen.blit(node_label, (10, y_offset))
        
        # Display each channel
        for ch_idx, channel in enumerate(assigned_channels):
            if sorted_node_distributions_type[node][ch_idx] == 's':
                ch_text = font.render(channel, True, signal_color)
            elif sorted_node_distributions_type[node][ch_idx] == 'i':
                ch_text = font.render(channel, True, idler_color)
            screen.blit(ch_text, (200 + ch_idx * 120, y_offset))
        y_offset += 80  # Move to the next row
    ch_text = font.render("Signal Channels", True, signal_color) 
    screen.blit(ch_text, (100, y_offset))
    ch_text = font.render("Idler Channels", True, idler_color) 
    screen.blit(ch_text, (100, y_offset+40))
    pygame.display.flip()

pygame.quit()