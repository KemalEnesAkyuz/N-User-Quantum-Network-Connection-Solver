import pygame
import sys
import os
from itertools import combinations
import numpy as np

# Initialize pygame
pygame.init()

# Set up display
initial_width, initial_height = 1600, 800
screen = pygame.display.set_mode((initial_width, initial_height), pygame.RESIZABLE)
pygame.display.set_caption("Channel Distributor for Quantum Key Distribution")

# Colors
black = (0, 0, 0)
white = (255, 255, 255)
label_color = (180, 180, 180)
highlight_color = (0, 115, 145, 150)  # Blue for diagonal
selected_color = (50, 115, 25)  # Green for selected cells

# Define font
font = pygame.font.SysFont(None, 24)

# Load settings from file, including 'n' (number of nodes in the network) (default to 4)
settings_file = "settings.txt"
channels_file = "channels.txt"
freq_cor_file = "freq_cor_latest.txt"
diagonal_select_channel = None
n = 4
selected_channels = set()  # Track selected cells on the diagonal

# Channel labels
channels = [f"C{i}" if j % 2 == 0 else f"H{i}" for i in range(14, 38) for j in range(2)]
num_channels = len(channels)

if os.path.exists(settings_file):
    with open(settings_file, "r") as file:
        lines = file.readlines()
        if lines:
            n = int(lines[1].strip())
            if len(lines) > 2:
                diagonal_select_channel = tuple(map(int, lines[3].strip().split(",")))
            if len(lines) > 5:
                selected_channels = {tuple(map(int, line.strip().split(","))) for line in lines[5:]}

if os.path.exists(channels_file):
    with open(channels_file, "r") as file:
        lines = file.readlines()
        if lines:
            possible_connections = []
            for line in lines[:]:
                possible_connections.append(line.strip()) 

frequency_matrix = []
corner_channels_number = []

if os.path.exists(freq_cor_file):
    with open(freq_cor_file, "r") as file:
        lines = file.readlines()
        if lines:
            corner_channels = lines[0].strip().split(",")
            corner_channels_number = [channels.index(corner_channels[0]),channels.index(corner_channels[1])]
            # Load the matrix values
            for line in lines[1:]:
                row = list(map(int, line.strip().split("\t")))
                frequency_matrix.append(row)

# Find min and max frequency values
freq_min = min(min(row) for row in frequency_matrix)
freq_max = max(max(row) for row in frequency_matrix)

# Cell size and table offset variables
cell_size = 30
table_offset = 60
zoom_level = 1.0
move_x, move_y = 0, 0  # Movement offset variables

# Variables for mouse drag functionality
dragging = False
last_mouse_pos = None

# Generate connection names for n nodes
nodes = [chr(65 + i) for i in range(n)]  # A, B, C, ...
if len(possible_connections) != int(n*(n-1)/2):
    print("Not enough (or too many) channels in the txt file!")
    print("Number of inputted channels: {}".format(len(possible_connections)))
    print("Number of channels needed due to {} nodes: {}".format(n, int(n*(n-1)/2)))
    possible_connections = [f"{a}{b}" for a, b in combinations(nodes, 2)]
connections = []  # Store assigned connection names
node_channels = {node: [] for node in nodes}  # Channels per node

if len(selected_channels) >= len(possible_connections):
    connections = possible_connections[:]
else:
    connections = []

# Function to display node-channel distribution in a new Pygame window
def show_node_distribution():
    dist_width, dist_height = 400, 400
    dist_screen = pygame.display.set_mode((dist_width, dist_height), pygame.RESIZABLE)
    pygame.display.set_caption("Node Channel Distribution")

    running_dist = True
    while running_dist:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_dist = False

        dist_screen.fill(black)
        
        # Draw headers for nodes
        for idx, node in enumerate(nodes):
            header = font.render(f"Node {node}", True, white)
            dist_screen.blit(header, (10, idx * 100 + 20))
            
            # Display channels for each node
            for jdx, ch in enumerate(node_channels[node]):
                channel_text = font.render(ch, True, selected_color)
                dist_screen.blit(channel_text, (10, idx * 100 + 50 + jdx * 20))

        pygame.display.flip()

def color_scale_1(freq,freq_min,freq_max):
    # Used for scaling the frequency correlation matrix highlighting
    if freq< freq_min + 0.0050*(freq_max-freq_min):
        return 0
    else:
        return int(255*(freq-freq_min)/(freq_max-freq_min))

def color_scale_2(color):
    # Used for scaling the diagonal and selected channel highlighting
    if color<150:
        return 150/255
    else:
        return color/255

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Save selected cell, `n`, and selected cells to settings file before quitting
            with open(settings_file, "w") as file:
                file.write(f"Number of nodes in the n-node Quantum Network:\n")
                file.write(f"{n}\n")
                file.write(f"The channel used for idenfitying selected diagonal\
                           (highest councidence):\n")
                if diagonal_select_channel:
                    file.write(f"{diagonal_select_channel[0]},{diagonal_select_channel[1]}\n")    
                file.write(f"Selected channels to be distributed to the nodes:\n")
                selected_channels_list = list(selected_channels)
                selected_channels_list = sorted(selected_channels_list, key=lambda x: x[1])
                for cell in selected_channels_list:
                    file.write(f"{cell[0]},{cell[1]}\n")
            with open(channels_file, "w") as file:
                for comb in possible_connections:
                    file.write(f"{comb}\n")
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEWHEEL:
            zoom_level += event.y * 0.1
            zoom_level = max(0.5, min(5.0, zoom_level))  # Limit zoom between 0.5x and 2x
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                move_y += 20
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                move_y -= 20
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                move_x += 20
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                move_x -= 20
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button for dragging
                dragging = True
                last_mouse_pos = event.pos
            elif event.button == 1:  # Left mouse button for setting primary diagonal
                mouse_x, mouse_y = event.pos
                # Adjust click to account for zoom level in both offsets and cell size
                clicked_col = int((mouse_x - table_offset * zoom_level - move_x) / (cell_size * zoom_level))
                clicked_row = int((mouse_y - table_offset * zoom_level - move_y) / (cell_size * zoom_level))
                if 0 <= clicked_col < num_channels and 0 <= clicked_row < num_channels:
                    diagonal_select_channel = (clicked_row, clicked_col)  # Set new primary diagonal
                    selected_channels.clear()  # Clear previously selected cells
                    connections.clear()  # Clear assigned connections
            elif event.button == 3:  # Right mouse button to select/deselect cells on the diagonal
                if diagonal_select_channel:
                    mouse_x, mouse_y = event.pos
                    clicked_col = int((mouse_x - table_offset * zoom_level - move_x) / (cell_size * zoom_level))
                    clicked_row = int((mouse_y - table_offset * zoom_level - move_y) / (cell_size * zoom_level))
                    # Ensure the click is on the primary anti-diagonal
                    if (clicked_row + clicked_col) == (diagonal_select_channel[0] + diagonal_select_channel[1]):
                        # Toggle the cell selection
                        if (clicked_row, clicked_col) in selected_channels:
                            selected_channels.remove((clicked_row, clicked_col))
                        else:
                            selected_channels.add((clicked_row, clicked_col))
                        # Assign connections when enough cells are selected
                        if len(selected_channels) >= len(possible_connections):
                            connections = possible_connections[:]
                        else:
                            connections = []
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            mouse_x, mouse_y = event.pos
            dx, dy = mouse_x - last_mouse_pos[0], mouse_y - last_mouse_pos[1]
            move_x += dx
            move_y += dy
            last_mouse_pos = (mouse_x, mouse_y)

    # Adjust cell size based on zoom level
    adjusted_cell_size = int(cell_size * zoom_level)
    adjusted_table_offset = int(table_offset * zoom_level)

    # Fill the background
    screen.fill(black)

    # Draw "Signal Photon Channels" and "Idler Photon Channels" labels
    signal_label = font.render("Signal Photon Channels", True, label_color)
    idler_label = font.render("Idler Photon Channels", True, label_color)
    screen.blit(signal_label, (10, table_offset + num_channels * adjusted_cell_size + move_y // 2))
    screen.blit(idler_label, (table_offset + num_channels * adjusted_cell_size + move_x // 2, 10))
    
    # Draw table grid and highlight cells
    for i in range(num_channels):
        for j in range(num_channels):
            highlight_color = (0, 115, 145, 150)  # Blue for diagonal
            selected_color = (50, 115, 25)  # Green for selected cells
            cell_rect = pygame.Rect(adjusted_table_offset + j * adjusted_cell_size + move_x,
                                    adjusted_table_offset + i * adjusted_cell_size + move_y,
                                    adjusted_cell_size, adjusted_cell_size)
            if (i>=corner_channels_number[0]) and (i<corner_channels_number[0]+len(frequency_matrix)):
                if (j>=corner_channels_number[1]) and (j<corner_channels_number[1]+len(frequency_matrix[0])):
                    i_p = i - corner_channels_number[0];
                    j_p = j - corner_channels_number[1];
                    color = (color_scale_1(frequency_matrix[i_p][j_p],freq_min,freq_max),
                             color_scale_1(frequency_matrix[i_p][j_p],freq_min,freq_max),
                             color_scale_1(frequency_matrix[i_p][j_p],freq_min,freq_max))
                    pygame.draw.rect(screen, color, cell_rect)
                    highlight_color = (int(highlight_color[0]*color_scale_2(color[0])),
                                     int(highlight_color[1]*color_scale_2(color[1])),
                                     int(highlight_color[2]*color_scale_2(color[2])))
                    selected_color = (int(selected_color[0]*color_scale_2(color[0])),
                                     int(selected_color[1]*color_scale_2(color[1])),
                                     int(selected_color[2]*color_scale_2(color[2])))
            # Highlight the main diagonal if selected
            if diagonal_select_channel and (i + j) == (diagonal_select_channel[0] + diagonal_select_channel[1]):
                color = selected_color if (i, j) in selected_channels else highlight_color
                pygame.draw.rect(screen, color, cell_rect)
            pygame.draw.rect(screen, white, cell_rect, 1)
    highlight_color = (0, 115, 145, 150)  # Blue for diagonal
    selected_color = (50, 115, 25)  # Green for selected cells       

    cell_rect = pygame.Rect(adjusted_table_offset + corner_channels_number[1] * adjusted_cell_size + move_x,
                                    adjusted_table_offset + corner_channels_number[0] * adjusted_cell_size + move_y,
                                    adjusted_cell_size*len(frequency_matrix), adjusted_cell_size*len(frequency_matrix[0]))
    pygame.draw.rect(screen, ((255,50,50)), cell_rect,5)

    # Display assigned connection names
    if len(selected_channels) > 0:
        for l in range(0,len(selected_channels)): 
            if len(connections) > 0:
                selected_channels_list = list(selected_channels)
                selected_channels_list = sorted(selected_channels_list, key=lambda x: x[1])
                (i,j) = selected_channels_list[l]
                cell_rect = pygame.Rect(adjusted_table_offset + j * adjusted_cell_size + move_x,
                                        adjusted_table_offset + i * adjusted_cell_size + move_y,
                                        adjusted_cell_size, adjusted_cell_size)
                idx = selected_channels_list.index((i, j))
                if idx < len(connections):
                    conn_text = font.render(connections[idx], True, white)
                    screen.blit(conn_text, (cell_rect.x + 3*zoom_level**2, cell_rect.y + 3*zoom_level**2))

    # Render fixed row and column labels
    for i, channel in enumerate(channels):
        row_label = font.render(channel, True, label_color)
        screen.blit(row_label, (10, adjusted_table_offset + i * adjusted_cell_size + adjusted_cell_size // 4 + move_y))

        col_label = font.render(channel, True, label_color)
        screen.blit(col_label, (adjusted_table_offset + i * adjusted_cell_size + adjusted_cell_size // 4 + move_x, 10))

    # Update display
    pygame.display.flip()
