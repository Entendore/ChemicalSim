"""
Chemical Reaction Simulator v4 - Pygame
========================================
A comprehensive, feature-rich interactive chemical reaction simulation
with 31 elements, 184 molecules, and 162+ active reaction pathways.

Controls:
  Left Click/Drag  - Use current tool
  Right Click      - Quick-spawn random atom
  Shift+Click      - Continuous emitter (spawn mode)
  1-0              - Select element 1-10
  Shift+1-0        - Select element 11-20
  Tab / Q / W      - Cycle tool mode
  R                - Reset simulation
  SPACE            - Pause / Resume
  +/-              - Simulation speed
  G                - Toggle gravity
  B                - Toggle molecule structure view
  T                - Cycle temperature preset
  H / J            - Heat / Cool at cursor
  M                - Toggle sound
  F12              - Screenshot
  Ctrl+Z           - Undo last spawn
  ESC              - Quit
"""

import pygame
import pygame.gfxdraw
import random
import math
import sys
import os
import struct
import io
import array
from collections import deque

# ─── Constants ────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1400, 900
SIM_WIDTH = 1000
PANEL_X = SIM_WIDTH
PANEL_WIDTH = WIDTH - SIM_WIDTH
FPS = 60
BG_BASE = (12, 12, 25)
PANEL_BG = (20, 20, 40)
PANEL_BORDER = (55, 55, 95)

# ─── Temperature presets ─────────────────────────────────────────────────────
TEMP_PRESETS = [
    {"name": "Cryogenic",  "temp": 50,    "color_mult": 0.4, "bg_tint": (0, 20, 60)},
    {"name": "Cold",       "temp": 150,   "color_mult": 0.6, "bg_tint": (0, 10, 40)},
    {"name": "Room Temp",  "temp": 300,   "color_mult": 1.0, "bg_tint": (0, 0, 0)},
    {"name": "Warm",       "temp": 500,   "color_mult": 1.3, "bg_tint": (20, 5, 0)},
    {"name": "Hot",        "temp": 1000,  "color_mult": 1.8, "bg_tint": (40, 10, 0)},
    {"name": "Plasma",     "temp": 3000,  "color_mult": 3.0, "bg_tint": (60, 15, 0)},
]

# ─── Atom Definitions ────────────────────────────────────────────────────────
ATOM_TYPES = {
    # --- Original 11 ---
    "H":  {"name": "Hydrogen",  "color": (200, 200, 255), "radius": 11, "mass": 1,  "valence": 1,  "electrons": 1,  "group": 1},
    "He": {"name": "Helium",    "color": (255, 255, 80),  "radius": 12, "mass": 4,  "valence": 0,  "electrons": 2,  "group": 18},
    "C":  {"name": "Carbon",    "color": (90, 90, 90),    "radius": 16, "mass": 12, "valence": 4,  "electrons": 6,  "group": 14},
    "N":  {"name": "Nitrogen",  "color": (70, 70, 255),   "radius": 15, "mass": 14, "valence": 3,  "electrons": 7,  "group": 15},
    "O":  {"name": "Oxygen",    "color": (255, 60, 60),   "radius": 14, "mass": 16, "valence": 2,  "electrons": 8,  "group": 16},
    "F":  {"name": "Fluorine",  "color": (60, 255, 60),   "radius": 13, "mass": 19, "valence": 1,  "electrons": 9,  "group": 17},
    "Na": {"name": "Sodium",    "color": (170, 70, 255),  "radius": 20, "mass": 23, "valence": 1,  "electrons": 11, "group": 1},
    "Cl": {"name": "Chlorine",  "color": (50, 210, 50),   "radius": 18, "mass": 35, "valence": 1,  "electrons": 17, "group": 17},
    "S":  {"name": "Sulfur",    "color": (255, 220, 50),  "radius": 17, "mass": 32, "valence": 2,  "electrons": 16, "group": 16},
    "Fe": {"name": "Iron",      "color": (180, 130, 80),  "radius": 19, "mass": 56, "valence": 3,  "electrons": 26, "group": 8},
    "Ca": {"name": "Calcium",   "color": (100, 200, 200), "radius": 21, "mass": 40, "valence": 2,  "electrons": 20, "group": 2},
    # --- New: Alkali / Alkaline Earth ---
    "Li": {"name": "Lithium",   "color": (220, 50, 50),   "radius": 15, "mass": 7,  "valence": 1,  "electrons": 3,  "group": 1},
    "Be": {"name": "Beryllium", "color": (0, 200, 150),   "radius": 14, "mass": 9,  "valence": 2,  "electrons": 4,  "group": 2},
    "Mg": {"name": "Magnesium", "color": (50, 180, 80),   "radius": 18, "mass": 24, "valence": 2,  "electrons": 12, "group": 2},
    "K":  {"name": "Potassium",  "color": (200, 120, 220), "radius": 23, "mass": 39, "valence": 1,  "electrons": 19, "group": 1},
    "Ba": {"name": "Barium",    "color": (120, 255, 120), "radius": 24, "mass": 137, "valence": 2, "electrons": 56, "group": 2},
    # --- New: Metalloids / Nonmetals ---
    "B":  {"name": "Boron",     "color": (240, 180, 220), "radius": 14, "mass": 11, "valence": 3,  "electrons": 5,  "group": 13},
    "Si": {"name": "Silicon",   "color": (160, 140, 120), "radius": 17, "mass": 28, "valence": 4,  "electrons": 14, "group": 14},
    "P":  {"name": "Phosphorus", "color": (255, 130, 30),  "radius": 16, "mass": 31, "valence": 3,  "electrons": 15, "group": 15},
    # --- New: Noble Gases ---
    "Ne": {"name": "Neon",      "color": (255, 100, 180), "radius": 12, "mass": 20, "valence": 0,  "electrons": 10, "group": 18},
    "Ar": {"name": "Argon",     "color": (180, 100, 255), "radius": 13, "mass": 40, "valence": 0,  "electrons": 18, "group": 18},
    # --- New: Transition Metals ---
    "Ti": {"name": "Titanium",  "color": (190, 190, 210), "radius": 20, "mass": 48, "valence": 4,  "electrons": 22, "group": 4},
    "Cr": {"name": "Chromium",  "color": (150, 150, 200), "radius": 19, "mass": 52, "valence": 3,  "electrons": 24, "group": 6},
    "Mn": {"name": "Manganese", "color": (200, 170, 130), "radius": 19, "mass": 55, "valence": 2,  "electrons": 25, "group": 7},
    "Ni": {"name": "Nickel",    "color": (170, 200, 150), "radius": 18, "mass": 59, "valence": 2,  "electrons": 28, "group": 10},
    "Cu": {"name": "Copper",    "color": (220, 140, 60),  "radius": 18, "mass": 64, "valence": 2,  "electrons": 29, "group": 11},
    "Zn": {"name": "Zinc",      "color": (180, 210, 180), "radius": 18, "mass": 65, "valence": 2,  "electrons": 30, "group": 12},
    "Ag": {"name": "Silver",    "color": (210, 210, 220), "radius": 19, "mass": 108, "valence": 1,  "electrons": 47, "group": 11},
    "Au": {"name": "Gold",      "color": (255, 215, 0),   "radius": 20, "mass": 197, "valence": 1,  "electrons": 79, "group": 11},
    # --- New: Halogens ---
    "Br": {"name": "Bromine",   "color": (180, 50, 50),   "radius": 19, "mass": 80, "valence": 1,  "electrons": 35, "group": 17},
    "I":  {"name": "Iodine",    "color": (130, 80, 200),  "radius": 21, "mass": 127, "valence": 1,  "electrons": 53, "group": 17},
}

# ─── Molecule Definitions ────────────────────────────────────────────────────
MOLECULE_TYPES = {
    # === Original 18 ===
    "H2":     {"formula": "H\u2082",           "color": (190, 190, 255), "radius": 15, "mass": 2,
               "atoms": ["H", "H"], "bond_order": [2], "decomp_temp": 2000,
               "decomp_products": [("H", 2)]},
    "O2":     {"formula": "O\u2082",           "color": (255, 90, 90),   "radius": 19, "mass": 32,
               "atoms": ["O", "O"], "bond_order": [2], "decomp_temp": 2500,
               "decomp_products": [("O", 2)]},
    "N2":     {"formula": "N\u2082",           "color": (110, 110, 255), "radius": 19, "mass": 28,
               "atoms": ["N", "N"], "bond_order": [3], "decomp_temp": 3000,
               "decomp_products": [("N", 2)]},
    "H2O":    {"formula": "H\u2082O",          "color": (70, 150, 255),  "radius": 21, "mass": 18,
               "atoms": ["H", "O", "H"], "bond_order": [1, 1], "decomp_temp": 2000,
               "decomp_products": [("H", 2), ("O", 1)]},
    "CO2":    {"formula": "CO\u2082",          "color": (160, 160, 160), "radius": 23, "mass": 44,
               "atoms": ["O", "C", "O"], "bond_order": [2, 2], "decomp_temp": 2500,
               "decomp_products": [("C", 1), ("O", 2)]},
    "NH3":    {"formula": "NH\u2083",          "color": (100, 100, 230), "radius": 22, "mass": 17,
               "atoms": ["N", "H", "H", "H"], "bond_order": [1, 1, 1], "decomp_temp": 1500,
               "decomp_products": [("N", 1), ("H", 3)]},
    "CH4":    {"formula": "CH\u2084",          "color": (150, 150, 150), "radius": 23, "mass": 16,
               "atoms": ["C", "H", "H", "H", "H"], "bond_order": [1, 1, 1, 1], "decomp_temp": 1200,
               "decomp_products": [("C", 1), ("H", 4)]},
    "HCl":    {"formula": "HCl",              "color": (130, 200, 130), "radius": 19, "mass": 36,
               "atoms": ["H", "Cl"], "bond_order": [1], "decomp_temp": 1800,
               "decomp_products": [("H", 1), ("Cl", 1)]},
    "NaCl":   {"formula": "NaCl",             "color": (150, 140, 200), "radius": 25, "mass": 58,
               "atoms": ["Na", "Cl"], "bond_order": [1], "decomp_temp": 1400,
               "decomp_products": [("Na", 1), ("Cl", 1)]},
    "HF":     {"formula": "HF",               "color": (90, 230, 90),   "radius": 17, "mass": 20,
               "atoms": ["H", "F"], "bond_order": [1], "decomp_temp": 2000,
               "decomp_products": [("H", 1), ("F", 1)]},
    "NO2":    {"formula": "NO\u2082",          "color": (210, 80, 210),  "radius": 21, "mass": 46,
               "atoms": ["N", "O", "O"], "bond_order": [2, 1], "decomp_temp": 1500,
               "decomp_products": [("N", 1), ("O", 2)]},
    "CO":     {"formula": "CO",               "color": (190, 140, 140), "radius": 20, "mass": 28,
               "atoms": ["C", "O"], "bond_order": [3], "decomp_temp": 2200,
               "decomp_products": [("C", 1), ("O", 1)]},
    "NaOH":   {"formula": "NaOH",             "color": (190, 110, 240), "radius": 25, "mass": 40,
               "atoms": ["Na", "O", "H"], "bond_order": [1, 1], "decomp_temp": 1600,
               "decomp_products": [("Na", 1), ("O", 1), ("H", 1)]},
    "H2S":    {"formula": "H\u2082S",          "color": (210, 200, 80),  "radius": 21, "mass": 34,
               "atoms": ["H", "S", "H"], "bond_order": [1, 1], "decomp_temp": 1400,
               "decomp_products": [("H", 2), ("S", 1)]},
    "SO2":    {"formula": "SO\u2082",          "color": (230, 200, 60),  "radius": 22, "mass": 64,
               "atoms": ["S", "O", "O"], "bond_order": [2, 2], "decomp_temp": 1800,
               "decomp_products": [("S", 1), ("O", 2)]},
    "FeO":    {"formula": "FeO",              "color": (200, 150, 100), "radius": 23, "mass": 72,
               "atoms": ["Fe", "O"], "bond_order": [2], "decomp_temp": 2000,
               "decomp_products": [("Fe", 1), ("O", 1)]},
    "CaO":    {"formula": "CaO",              "color": (140, 210, 210), "radius": 24, "mass": 56,
               "atoms": ["Ca", "O"], "bond_order": [2], "decomp_temp": 2600,
               "decomp_products": [("Ca", 1), ("O", 1)]},
    "CaCO3":  {"formula": "CaCO\u2083",       "color": (180, 200, 180), "radius": 28, "mass": 100,
               "atoms": ["Ca", "C", "O", "O", "O"], "bond_order": [1, 2, 1, 1], "decomp_temp": 900,
               "decomp_products": [("Ca", 1), ("C", 1), ("O", 3)]},
    # === New 1-10: Diatomics & Simple Hydrides ===
    "Br2":    {"formula": "Br\u2082",          "color": (200, 80, 80),   "radius": 22, "mass": 160,
               "atoms": ["Br", "Br"], "bond_order": [1], "decomp_temp": 1500,
               "decomp_products": [("Br", 2)]},
    "I2":     {"formula": "I\u2082",           "color": (160, 110, 220), "radius": 24, "mass": 254,
               "atoms": ["I", "I"], "bond_order": [1], "decomp_temp": 1200,
               "decomp_products": [("I", 2)]},
    "HBr":    {"formula": "HBr",             "color": (180, 150, 130), "radius": 20, "mass": 81,
               "atoms": ["H", "Br"], "bond_order": [1], "decomp_temp": 1600,
               "decomp_products": [("H", 1), ("Br", 1)]},
    "HI":     {"formula": "HI",              "color": (170, 130, 220), "radius": 21, "mass": 128,
               "atoms": ["H", "I"], "bond_order": [1], "decomp_temp": 1400,
               "decomp_products": [("H", 1), ("I", 1)]},
    "PH3":    {"formula": "PH\u2083",          "color": (230, 160, 60),  "radius": 22, "mass": 34,
               "atoms": ["P", "H", "H", "H"], "bond_order": [1, 1, 1], "decomp_temp": 1100,
               "decomp_products": [("P", 1), ("H", 3)]},
    "SiH4":   {"formula": "SiH\u2084",         "color": (170, 155, 140), "radius": 23, "mass": 32,
               "atoms": ["Si", "H", "H", "H", "H"], "bond_order": [1, 1, 1, 1], "decomp_temp": 1000,
               "decomp_products": [("Si", 1), ("H", 4)]},
    # === New 11-20: Oxides ===
    "Li2O":   {"formula": "Li\u2082O",         "color": (230, 100, 100), "radius": 22, "mass": 30,
               "atoms": ["Li", "Li", "O"], "bond_order": [1, 1], "decomp_temp": 1600,
               "decomp_products": [("Li", 2), ("O", 1)]},
    "BeO":    {"formula": "BeO",              "color": (60, 220, 170),  "radius": 18, "mass": 25,
               "atoms": ["Be", "O"], "bond_order": [2], "decomp_temp": 2800,
               "decomp_products": [("Be", 1), ("O", 1)]},
    "MgO":    {"formula": "MgO",             "color": (80, 200, 110),  "radius": 22, "mass": 40,
               "atoms": ["Mg", "O"], "bond_order": [2], "decomp_temp": 3100,
               "decomp_products": [("Mg", 1), ("O", 1)]},
    "K2O":    {"formula": "K\u2082O",          "color": (210, 140, 230), "radius": 26, "mass": 94,
               "atoms": ["K", "K", "O"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("K", 2), ("O", 1)]},
    "BaO":    {"formula": "BaO",             "color": (140, 255, 140), "radius": 27, "mass": 153,
               "atoms": ["Ba", "O"], "bond_order": [2], "decomp_temp": 2000,
               "decomp_products": [("Ba", 1), ("O", 1)]},
    "SiO2":   {"formula": "SiO\u2082",         "color": (180, 160, 140), "radius": 24, "mass": 60,
               "atoms": ["Si", "O", "O"], "bond_order": [2, 2], "decomp_temp": 2500,
               "decomp_products": [("Si", 1), ("O", 2)]},
    "TiO2":   {"formula": "TiO\u2082",         "color": (200, 200, 220), "radius": 26, "mass": 80,
               "atoms": ["Ti", "O", "O"], "bond_order": [2, 2], "decomp_temp": 2100,
               "decomp_products": [("Ti", 1), ("O", 2)]},
    "Cr2O3":  {"formula": "Cr\u2082O\u2083",    "color": (170, 170, 220), "radius": 28, "mass": 152,
               "atoms": ["Cr", "Cr", "O", "O", "O"], "bond_order": [1, 1, 2, 1], "decomp_temp": 2400,
               "decomp_products": [("Cr", 2), ("O", 3)]},
    "MnO2":   {"formula": "MnO\u2082",         "color": (210, 190, 150), "radius": 24, "mass": 87,
               "atoms": ["Mn", "O", "O"], "bond_order": [2, 2], "decomp_temp": 1600,
               "decomp_products": [("Mn", 1), ("O", 2)]},
    "NiO":    {"formula": "NiO",             "color": (180, 210, 160), "radius": 22, "mass": 75,
               "atoms": ["Ni", "O"], "bond_order": [2], "decomp_temp": 2200,
               "decomp_products": [("Ni", 1), ("O", 1)]},
    # === New 21-30: More Oxides + Halides ===
    "CuO":    {"formula": "CuO",             "color": (230, 160, 80),  "radius": 22, "mass": 80,
               "atoms": ["Cu", "O"], "bond_order": [2], "decomp_temp": 1500,
               "decomp_products": [("Cu", 1), ("O", 1)]},
    "ZnO":    {"formula": "ZnO",             "color": (190, 220, 190), "radius": 22, "mass": 81,
               "atoms": ["Zn", "O"], "bond_order": [2], "decomp_temp": 1975,
               "decomp_products": [("Zn", 1), ("O", 1)]},
    "Ag2O":   {"formula": "Ag\u2082O",         "color": (220, 220, 230), "radius": 24, "mass": 232,
               "atoms": ["Ag", "Ag", "O"], "bond_order": [1, 1], "decomp_temp": 600,
               "decomp_products": [("Ag", 2), ("O", 1)]},
    "Fe2O3":  {"formula": "Fe\u2082O\u2083",    "color": (210, 160, 110), "radius": 28, "mass": 160,
               "atoms": ["Fe", "Fe", "O", "O", "O"], "bond_order": [1, 1, 2, 1], "decomp_temp": 1800,
               "decomp_products": [("Fe", 2), ("O", 3)]},
    "LiF":    {"formula": "LiF",             "color": (240, 100, 100), "radius": 17, "mass": 26,
               "atoms": ["Li", "F"], "bond_order": [1], "decomp_temp": 1700,
               "decomp_products": [("Li", 1), ("F", 1)]},
    "LiCl":   {"formula": "LiCl",            "color": (200, 130, 170), "radius": 20, "mass": 42,
               "atoms": ["Li", "Cl"], "bond_order": [1], "decomp_temp": 1400,
               "decomp_products": [("Li", 1), ("Cl", 1)]},
    "MgCl2":  {"formula": "MgCl\u2082",       "color": (100, 200, 140), "radius": 23, "mass": 95,
               "atoms": ["Mg", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1500,
               "decomp_products": [("Mg", 1), ("Cl", 2)]},
    "KCl":    {"formula": "KCl",             "color": (180, 150, 230), "radius": 24, "mass": 74,
               "atoms": ["K", "Cl"], "bond_order": [1], "decomp_temp": 1400,
               "decomp_products": [("K", 1), ("Cl", 1)]},
    "CuCl2":  {"formula": "CuCl\u2082",       "color": (220, 170, 100), "radius": 23, "mass": 134,
               "atoms": ["Cu", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Cu", 1), ("Cl", 2)]},
    "ZnCl2":  {"formula": "ZnCl\u2082",       "color": (170, 210, 170), "radius": 23, "mass": 136,
               "atoms": ["Zn", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1300,
               "decomp_products": [("Zn", 1), ("Cl", 2)]},
    # === New 31-40: Hydroxides, Sulfides, Acids, More ===
    "LiOH":   {"formula": "LiOH",            "color": (230, 120, 180), "radius": 22, "mass": 24,
               "atoms": ["Li", "O", "H"], "bond_order": [1, 1], "decomp_temp": 1300,
               "decomp_products": [("Li", 1), ("O", 1), ("H", 1)]},
    "KOH":    {"formula": "KOH",             "color": (200, 150, 240), "radius": 26, "mass": 56,
               "atoms": ["K", "O", "H"], "bond_order": [1, 1], "decomp_temp": 1300,
               "decomp_products": [("K", 1), ("O", 1), ("H", 1)]},
    "MgS":    {"formula": "MgS",             "color": (140, 210, 120), "radius": 22, "mass": 56,
               "atoms": ["Mg", "S"], "bond_order": [2], "decomp_temp": 2000,
               "decomp_products": [("Mg", 1), ("S", 1)]},
    "ZnS":    {"formula": "ZnS",             "color": (200, 220, 140), "radius": 22, "mass": 97,
               "atoms": ["Zn", "S"], "bond_order": [2], "decomp_temp": 1700,
               "decomp_products": [("Zn", 1), ("S", 1)]},
    "FeS":    {"formula": "FeS",             "color": (200, 170, 110), "radius": 23, "mass": 88,
               "atoms": ["Fe", "S"], "bond_order": [2], "decomp_temp": 1800,
               "decomp_products": [("Fe", 1), ("S", 1)]},
    "CaS":    {"formula": "CaS",             "color": (130, 220, 180), "radius": 24, "mass": 72,
               "atoms": ["Ca", "S"], "bond_order": [2], "decomp_temp": 2000,
               "decomp_products": [("Ca", 1), ("S", 1)]},
    "CaCl2":  {"formula": "CaCl\u2082",       "color": (120, 190, 190), "radius": 26, "mass": 111,
               "atoms": ["Ca", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1800,
               "decomp_products": [("Ca", 1), ("Cl", 2)]},
    "NaF":    {"formula": "NaF",             "color": (160, 140, 255), "radius": 22, "mass": 42,
               "atoms": ["Na", "F"], "bond_order": [1], "decomp_temp": 1700,
               "decomp_products": [("Na", 1), ("F", 1)]},
    "Na2S":   {"formula": "Na\u2082S",         "color": (180, 160, 220), "radius": 25, "mass": 78,
               "atoms": ["Na", "Na", "S"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Na", 2), ("S", 1)]},
    "H2O2":   {"formula": "H\u2082O\u2082",    "color": (100, 180, 220), "radius": 22, "mass": 34,
               "atoms": ["H", "O", "O", "H"], "bond_order": [1, 1, 1], "decomp_temp": 700,
               "decomp_products": [("H", 2), ("O", 2)]},
    # === New 41-43: Bonus molecules ===
    "N2O":    {"formula": "N\u2082O",          "color": (150, 130, 255), "radius": 22, "mass": 44,
               "atoms": ["N", "N", "O"], "bond_order": [3, 1], "decomp_temp": 1200,
               "decomp_products": [("N", 2), ("O", 1)]},
    "NO":     {"formula": "NO",              "color": (180, 100, 200), "radius": 20, "mass": 30,
               "atoms": ["N", "O"], "bond_order": [2], "decomp_temp": 1300,
               "decomp_products": [("N", 1), ("O", 1)]},
    "AgCl":   {"formula": "AgCl",            "color": (220, 220, 230), "radius": 23, "mass": 143,
               "atoms": ["Ag", "Cl"], "bond_order": [1], "decomp_temp": 800,
               "decomp_products": [("Ag", 1), ("Cl", 1)]},
    "FeCl3":  {"formula": "FeCl\u2083",       "color": (190, 160, 120), "radius": 25, "mass": 162,
               "atoms": ["Fe", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1], "decomp_temp": 600,
               "decomp_products": [("Fe", 1), ("Cl", 3)]},
    "HNO3":   {"formula": "HNO\u2083",         "color": (180, 100, 200), "radius": 25, "mass": 63,
               "atoms": ["H", "N", "O", "O", "O"], "bond_order": [1, 1, 2, 1], "decomp_temp": 500,
               "decomp_products": [("H", 1), ("N", 1), ("O", 3)]},
    "SO3":    {"formula": "SO\u2083",          "color": (240, 210, 80),  "radius": 24, "mass": 80,
               "atoms": ["S", "O", "O", "O"], "bond_order": [2, 2, 2], "decomp_temp": 1600,
               "decomp_products": [("S", 1), ("O", 3)]},
    "C2H2":   {"formula": "C\u2082H\u2082",     "color": (130, 130, 130), "radius": 20, "mass": 26,
               "atoms": ["C", "C", "H", "H"], "bond_order": [3, 1, 1], "decomp_temp": 1100,
               "decomp_products": [("C", 2), ("H", 2)]},
    # === New batch 2: Interhalogens ===
    "BrCl":   {"formula": "BrCl",            "color": (120, 140, 60),  "radius": 21, "mass": 115,
               "atoms": ["Br", "Cl"], "bond_order": [1], "decomp_temp": 1000,
               "decomp_products": [("Br", 1), ("Cl", 1)]},
    "ICl":    {"formula": "ICl",             "color": (100, 90, 160),  "radius": 22, "mass": 162,
               "atoms": ["I", "Cl"], "bond_order": [1], "decomp_temp": 800,
               "decomp_products": [("I", 1), ("Cl", 1)]},
    "ClF":    {"formula": "ClF",             "color": (50, 200, 60),  "radius": 17, "mass": 54,
               "atoms": ["Cl", "F"], "bond_order": [1], "decomp_temp": 1100,
               "decomp_products": [("Cl", 1), ("F", 1)]},
    # === New batch 2: Alkali halides (Br/I) ===
    "LiBr":   {"formula": "LiBr",           "color": (210, 100, 100), "radius": 20, "mass": 87,
               "atoms": ["Li", "Br"], "bond_order": [1], "decomp_temp": 1300,
               "decomp_products": [("Li", 1), ("Br", 1)]},
    "LiI":    {"formula": "LiI",             "color": (190, 100, 180), "radius": 21, "mass": 134,
               "atoms": ["Li", "I"], "bond_order": [1], "decomp_temp": 1100,
               "decomp_products": [("Li", 1), ("I", 1)]},
    "NaBr":   {"formula": "NaBr",           "color": (130, 140, 180), "radius": 24, "mass": 103,
               "atoms": ["Na", "Br"], "bond_order": [1], "decomp_temp": 1300,
               "decomp_products": [("Na", 1), ("Br", 1)]},
    "NaI":    {"formula": "NaI",             "color": (120, 130, 210), "radius": 24, "mass": 150,
               "atoms": ["Na", "I"], "bond_order": [1], "decomp_temp": 1100,
               "decomp_products": [("Na", 1), ("I", 1)]},
    "KBr":    {"formula": "KBr",            "color": (190, 120, 200), "radius": 25, "mass": 119,
               "atoms": ["K", "Br"], "bond_order": [1], "decomp_temp": 1300,
               "decomp_products": [("K", 1), ("Br", 1)]},
    "KI":     {"formula": "KI",             "color": (180, 110, 220), "radius": 26, "mass": 166,
               "atoms": ["K", "I"], "bond_order": [1], "decomp_temp": 1100,
               "decomp_products": [("K", 1), ("I", 1)]},
    # === New batch 2: Alkali/alkaline-earth sulfides & fluorides ===
    "Li2S":   {"formula": "Li\u2082S",        "color": (220, 150, 100), "radius": 22, "mass": 46,
               "atoms": ["Li", "Li", "S"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Li", 2), ("S", 1)]},
    "K2S":    {"formula": "K\u2082S",         "color": (200, 170, 150), "radius": 27, "mass": 110,
               "atoms": ["K", "K", "S"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("K", 2), ("S", 1)]},
    "MgF2":   {"formula": "MgF\u2082",       "color": (70, 210, 100),  "radius": 22, "mass": 62,
               "atoms": ["Mg", "F", "F"], "bond_order": [1, 1], "decomp_temp": 2200,
               "decomp_products": [("Mg", 1), ("F", 2)]},
    "KF":     {"formula": "KF",             "color": (190, 140, 230), "radius": 23, "mass": 58,
               "atoms": ["K", "F"], "bond_order": [1], "decomp_temp": 1500,
               "decomp_products": [("K", 1), ("F", 1)]},
    "BaCl2":  {"formula": "BaCl\u2082",      "color": (110, 230, 130), "radius": 28, "mass": 208,
               "atoms": ["Ba", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1500,
               "decomp_products": [("Ba", 1), ("Cl", 2)]},
    "BaF2":   {"formula": "BaF\u2082",       "color": (100, 240, 120), "radius": 27, "mass": 175,
               "atoms": ["Ba", "F", "F"], "bond_order": [1, 1], "decomp_temp": 1800,
               "decomp_products": [("Ba", 1), ("F", 2)]},
    "BeF2":   {"formula": "BeF\u2082",       "color": (40, 220, 160),  "radius": 18, "mass": 47,
               "atoms": ["Be", "F", "F"], "bond_order": [1, 1], "decomp_temp": 2000,
               "decomp_products": [("Be", 1), ("F", 2)]},
    "BeS":    {"formula": "BeS",            "color": (50, 210, 150),  "radius": 17, "mass": 41,
               "atoms": ["Be", "S"], "bond_order": [2], "decomp_temp": 2000,
               "decomp_products": [("Be", 1), ("S", 1)]},
    "CaF2":   {"formula": "CaF\u2082",       "color": (80, 200, 200),  "radius": 26, "mass": 78,
               "atoms": ["Ca", "F", "F"], "bond_order": [1, 1], "decomp_temp": 2000,
               "decomp_products": [("Ca", 1), ("F", 2)]},
    # === New batch 2: Transition metal halides/fluorides/sulfides ===
    "TiCl4":  {"formula": "TiCl\u2084",      "color": (180, 190, 220), "radius": 28, "mass": 190,
               "atoms": ["Ti", "Cl", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1, 1], "decomp_temp": 500,
               "decomp_products": [("Ti", 1), ("Cl", 4)]},
    "TiF4":   {"formula": "TiF\u2084",       "color": (170, 200, 210), "radius": 26, "mass": 124,
               "atoms": ["Ti", "F", "F", "F", "F"], "bond_order": [1, 1, 1, 1], "decomp_temp": 800,
               "decomp_products": [("Ti", 1), ("F", 4)]},
    "TiN":    {"formula": "TiN",             "color": (200, 195, 200), "radius": 23, "mass": 62,
               "atoms": ["Ti", "N"], "bond_order": [3], "decomp_temp": 2900,
               "decomp_products": [("Ti", 1), ("N", 1)]},
    "CrCl3":  {"formula": "CrCl\u2083",      "color": (140, 160, 200), "radius": 26, "mass": 158,
               "atoms": ["Cr", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1], "decomp_temp": 1000,
               "decomp_products": [("Cr", 1), ("Cl", 3)]},
    "CrF3":   {"formula": "CrF\u2083",       "color": (120, 180, 130), "radius": 24, "mass": 108,
               "atoms": ["Cr", "F", "F", "F"], "bond_order": [1, 1, 1], "decomp_temp": 1200,
               "decomp_products": [("Cr", 1), ("F", 3)]},
    "Cr2S3":  {"formula": "Cr\u2082S\u2083",   "color": (160, 165, 140), "radius": 28, "mass": 200,
               "atoms": ["Cr", "Cr", "S", "S", "S"], "bond_order": [1, 1, 2, 1], "decomp_temp": 1500,
               "decomp_products": [("Cr", 2), ("S", 3)]},
    "MnCl2":  {"formula": "MnCl\u2082",      "color": (190, 180, 140), "radius": 24, "mass": 126,
               "atoms": ["Mn", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Mn", 1), ("Cl", 2)]},
    "MnF2":   {"formula": "MnF\u2082",       "color": (150, 200, 110), "radius": 22, "mass": 93,
               "atoms": ["Mn", "F", "F"], "bond_order": [1, 1], "decomp_temp": 1400,
               "decomp_products": [("Mn", 1), ("F", 2)]},
    "MnS":    {"formula": "MnS",            "color": (200, 185, 130), "radius": 22, "mass": 87,
               "atoms": ["Mn", "S"], "bond_order": [2], "decomp_temp": 1800,
               "decomp_products": [("Mn", 1), ("S", 1)]},
    "NiCl2":  {"formula": "NiCl\u2082",      "color": (150, 190, 140), "radius": 23, "mass": 130,
               "atoms": ["Ni", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Ni", 1), ("Cl", 2)]},
    "NiF2":   {"formula": "NiF\u2082",       "color": (120, 210, 120), "radius": 21, "mass": 97,
               "atoms": ["Ni", "F", "F"], "bond_order": [1, 1], "decomp_temp": 1400,
               "decomp_products": [("Ni", 1), ("F", 2)]},
    "NiS":    {"formula": "NiS",            "color": (160, 195, 130), "radius": 21, "mass": 91,
               "atoms": ["Ni", "S"], "bond_order": [2], "decomp_temp": 1800,
               "decomp_products": [("Ni", 1), ("S", 1)]},
    "CuS":    {"formula": "CuS",            "color": (220, 150, 70),  "radius": 22, "mass": 96,
               "atoms": ["Cu", "S"], "bond_order": [2], "decomp_temp": 1500,
               "decomp_products": [("Cu", 1), ("S", 1)]},
    "CuF2":   {"formula": "CuF\u2082",       "color": (180, 180, 60),  "radius": 22, "mass": 102,
               "atoms": ["Cu", "F", "F"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Cu", 1), ("F", 2)]},
    "ZnF2":   {"formula": "ZnF\u2082",       "color": (130, 220, 130), "radius": 22, "mass": 103,
               "atoms": ["Zn", "F", "F"], "bond_order": [1, 1], "decomp_temp": 1500,
               "decomp_products": [("Zn", 1), ("F", 2)]},
    "Ag2S":   {"formula": "Ag\u2082S",       "color": (190, 190, 150), "radius": 24, "mass": 248,
               "atoms": ["Ag", "Ag", "S"], "bond_order": [1, 1], "decomp_temp": 800,
               "decomp_products": [("Ag", 2), ("S", 1)]},
    "AgF":    {"formula": "AgF",            "color": (200, 200, 210), "radius": 20, "mass": 127,
               "atoms": ["Ag", "F"], "bond_order": [1], "decomp_temp": 1200,
               "decomp_products": [("Ag", 1), ("F", 1)]},
    "FeF3":   {"formula": "FeF\u2083",       "color": (160, 170, 80),  "radius": 24, "mass": 113,
               "atoms": ["Fe", "F", "F", "F"], "bond_order": [1, 1, 1], "decomp_temp": 1000,
               "decomp_products": [("Fe", 1), ("F", 3)]},
    "AuCl3":  {"formula": "AuCl\u2083",      "color": (230, 200, 40),  "radius": 26, "mass": 303,
               "atoms": ["Au", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1], "decomp_temp": 500,
               "decomp_products": [("Au", 1), ("Cl", 3)]},
    # === New batch 2: Nonmetal halides & other compounds ===
    "SiCl4":  {"formula": "SiCl\u2084",      "color": (140, 150, 130), "radius": 27, "mass": 170,
               "atoms": ["Si", "Cl", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1, 1], "decomp_temp": 600,
               "decomp_products": [("Si", 1), ("Cl", 4)]},
    "SiF4":   {"formula": "SiF\u2084",       "color": (120, 180, 110), "radius": 24, "mass": 104,
               "atoms": ["Si", "F", "F", "F", "F"], "bond_order": [1, 1, 1, 1], "decomp_temp": 800,
               "decomp_products": [("Si", 1), ("F", 4)]},
    "SiC":    {"formula": "SiC",            "color": (150, 140, 130), "radius": 21, "mass": 40,
               "atoms": ["Si", "C"], "bond_order": [3], "decomp_temp": 2700,
               "decomp_products": [("Si", 1), ("C", 1)]},
    "PCl3":   {"formula": "PCl\u2083",       "color": (220, 150, 50),  "radius": 25, "mass": 137,
               "atoms": ["P", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1], "decomp_temp": 700,
               "decomp_products": [("P", 1), ("Cl", 3)]},
    "PF3":    {"formula": "PF\u2083",        "color": (100, 210, 50),  "radius": 22, "mass": 88,
               "atoms": ["P", "F", "F", "F"], "bond_order": [1, 1, 1], "decomp_temp": 900,
               "decomp_products": [("P", 1), ("F", 3)]},
    "BCl3":   {"formula": "BCl\u2083",       "color": (200, 160, 180), "radius": 23, "mass": 117,
               "atoms": ["B", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1], "decomp_temp": 500,
               "decomp_products": [("B", 1), ("Cl", 3)]},
    "BN":     {"formula": "BN",              "color": (200, 170, 210), "radius": 19, "mass": 25,
               "atoms": ["B", "N"], "bond_order": [3], "decomp_temp": 2500,
               "decomp_products": [("B", 1), ("N", 1)]},
    "CCl4":   {"formula": "CCl\u2084",       "color": (120, 120, 120), "radius": 26, "mass": 154,
               "atoms": ["C", "Cl", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1, 1], "decomp_temp": 500,
               "decomp_products": [("C", 1), ("Cl", 4)]},
    "CF4":    {"formula": "CF\u2084",        "color": (80, 150, 80),   "radius": 23, "mass": 88,
               "atoms": ["C", "F", "F", "F", "F"], "bond_order": [1, 1, 1, 1], "decomp_temp": 700,
               "decomp_products": [("C", 1), ("F", 4)]},
    "NF3":    {"formula": "NF\u2083",        "color": (80, 80, 220),   "radius": 22, "mass": 71,
               "atoms": ["N", "F", "F", "F"], "bond_order": [1, 1, 1], "decomp_temp": 1000,
               "decomp_products": [("N", 1), ("F", 3)]},
    "SF2":    {"formula": "SF\u2082",        "color": (220, 210, 60),  "radius": 20, "mass": 70,
               "atoms": ["S", "F", "F"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("S", 1), ("F", 2)]},
    "SCl2":   {"formula": "SCl\u2082",       "color": (200, 200, 60),  "radius": 22, "mass": 103,
               "atoms": ["S", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 1000,
               "decomp_products": [("S", 1), ("Cl", 2)]},
    "CS2":    {"formula": "CS\u2082",        "color": (180, 170, 40),  "radius": 23, "mass": 76,
               "atoms": ["C", "S", "S"], "bond_order": [2, 2], "decomp_temp": 1000,
               "decomp_products": [("C", 1), ("S", 2)]},
    "Li3N":   {"formula": "Li\u2083N",       "color": (230, 80, 120),  "radius": 23, "mass": 35,
               "atoms": ["Li", "Li", "Li", "N"], "bond_order": [1, 1, 1], "decomp_temp": 1000,
               "decomp_products": [("Li", 3), ("N", 1)]},
    "Mg3N2":  {"formula": "Mg\u2083N\u2082",   "color": (90, 190, 100),  "radius": 27, "mass": 100,
               "atoms": ["Mg", "Mg", "Mg", "N", "N"], "bond_order": [1, 1, 1, 2], "decomp_temp": 1500,
               "decomp_products": [("Mg", 3), ("N", 2)]},
    "MgBr2":  {"formula": "MgBr\u2082",      "color": (110, 180, 100), "radius": 25, "mass": 184,
               "atoms": ["Mg", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Mg", 1), ("Br", 2)]},
    "CaBr2":  {"formula": "CaBr\u2082",      "color": (100, 190, 170), "radius": 28, "mass": 200,
               "atoms": ["Ca", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 1400,
               "decomp_products": [("Ca", 1), ("Br", 2)]},
    "Cu2O":   {"formula": "Cu\u2082O",       "color": (240, 180, 100), "radius": 24, "mass": 144,
               "atoms": ["Cu", "Cu", "O"], "bond_order": [1, 1], "decomp_temp": 1800,
               "decomp_products": [("Cu", 2), ("O", 1)]},
    # === New batch 3: Hydrides ===
    "NaH":    {"formula": "NaH",             "color": (200, 100, 230), "radius": 22, "mass": 24,
               "atoms": ["Na", "H"], "bond_order": [1], "decomp_temp": 700,
               "decomp_products": [("Na", 1), ("H", 1)]},
    "KH":     {"formula": "KH",              "color": (210, 130, 230), "radius": 23, "mass": 40,
               "atoms": ["K", "H"], "bond_order": [1], "decomp_temp": 600,
               "decomp_products": [("K", 1), ("H", 1)]},
    "LiH":    {"formula": "LiH",             "color": (230, 70, 100), "radius": 16, "mass": 8,
               "atoms": ["Li", "H"], "bond_order": [1], "decomp_temp": 900,
               "decomp_products": [("Li", 1), ("H", 1)]},
    "MgH2":   {"formula": "MgH\u2082",       "color": (70, 200, 120), "radius": 21, "mass": 26,
               "atoms": ["Mg", "H", "H"], "bond_order": [1, 1], "decomp_temp": 500,
               "decomp_products": [("Mg", 1), ("H", 2)]},
    "CaH2":   {"formula": "CaH\u2082",       "color": (110, 210, 210), "radius": 24, "mass": 42,
               "atoms": ["Ca", "H", "H"], "bond_order": [1, 1], "decomp_temp": 600,
               "decomp_products": [("Ca", 1), ("H", 2)]},
    "TiH2":   {"formula": "TiH\u2082",       "color": (200, 195, 200), "radius": 23, "mass": 50,
               "atoms": ["Ti", "H", "H"], "bond_order": [1, 1], "decomp_temp": 800,
               "decomp_products": [("Ti", 1), ("H", 2)]},
    # === New batch 3: More oxides ===
    "Na2O":   {"formula": "Na\u2082O",       "color": (190, 90, 240), "radius": 24, "mass": 62,
               "atoms": ["Na", "Na", "O"], "bond_order": [1, 1], "decomp_temp": 1400,
               "decomp_products": [("Na", 2), ("O", 1)]},
    "OF2":    {"formula": "OF\u2082",        "color": (200, 140, 60),  "radius": 19, "mass": 54,
               "atoms": ["O", "F", "F"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("O", 1), ("F", 2)]},
    "ClO2":   {"formula": "ClO\u2082",       "color": (160, 200, 60), "radius": 20, "mass": 67,
               "atoms": ["Cl", "O", "O"], "bond_order": [2, 1], "decomp_temp": 600,
               "decomp_products": [("Cl", 1), ("O", 2)]},
    "B2O3":   {"formula": "B\u2082O\u2083",   "color": (230, 170, 200), "radius": 24, "mass": 70,
               "atoms": ["B", "B", "O", "O", "O"], "bond_order": [1, 1, 2, 1], "decomp_temp": 1800,
               "decomp_products": [("B", 2), ("O", 3)]},
    "P2O5":   {"formula": "P\u2082O\u2085",   "color": (240, 160, 40),  "radius": 27, "mass": 142,
               "atoms": ["P", "P", "O", "O", "O", "O", "O"], "bond_order": [1, 1, 2, 2, 2, 1], "decomp_temp": 1500,
               "decomp_products": [("P", 2), ("O", 5)]},
    # === New batch 3: Carbides ===
    "TiC":    {"formula": "TiC",             "color": (195, 195, 200), "radius": 22, "mass": 60,
               "atoms": ["Ti", "C"], "bond_order": [3], "decomp_temp": 3100,
               "decomp_products": [("Ti", 1), ("C", 1)]},
    "Fe3C":   {"formula": "Fe\u2083C",       "color": (195, 145, 95),  "radius": 27, "mass": 180,
               "atoms": ["Fe", "Fe", "Fe", "C"], "bond_order": [1, 1, 1], "decomp_temp": 1800,
               "decomp_products": [("Fe", 3), ("C", 1)]},
    "CaC2":   {"formula": "CaC\u2082",       "color": (130, 200, 190), "radius": 25, "mass": 64,
               "atoms": ["Ca", "C", "C"], "bond_order": [1, 2], "decomp_temp": 1600,
               "decomp_products": [("Ca", 1), ("C", 2)]},
    "B4C":    {"formula": "B\u2084C",        "color": (210, 175, 200), "radius": 24, "mass": 56,
               "atoms": ["B", "B", "B", "B", "C"], "bond_order": [1, 1, 1, 1], "decomp_temp": 2600,
               "decomp_products": [("B", 4), ("C", 1)]},
    "Cr3C2":  {"formula": "Cr\u2083C\u2082",   "color": (155, 155, 200), "radius": 27, "mass": 180,
               "atoms": ["Cr", "Cr", "Cr", "C", "C"], "bond_order": [1, 1, 1, 1], "decomp_temp": 2000,
               "decomp_products": [("Cr", 3), ("C", 2)]},
    "SiC2":   {"formula": "SiC\u2082",       "color": (155, 145, 130), "radius": 23, "mass": 52,
               "atoms": ["Si", "C", "C"], "bond_order": [1, 2], "decomp_temp": 1500,
               "decomp_products": [("Si", 1), ("C", 2)]},
    # === New batch 3: Sulfur compounds ===
    "S8":     {"formula": "S\u2088",         "color": (255, 230, 60),  "radius": 30, "mass": 256,
               "atoms": ["S", "S", "S", "S", "S", "S", "S", "S"], "bond_order": [1, 1, 1, 1, 1, 1, 1, 1], "decomp_temp": 800,
               "decomp_products": [("S", 8)]},
    "SiS2":   {"formula": "SiS\u2082",       "color": (170, 160, 120), "radius": 23, "mass": 92,
               "atoms": ["Si", "S", "S"], "bond_order": [2, 2], "decomp_temp": 1200,
               "decomp_products": [("Si", 1), ("S", 2)]},
    "TiS2":   {"formula": "TiS\u2082",       "color": (185, 185, 195), "radius": 25, "mass": 112,
               "atoms": ["Ti", "S", "S"], "bond_order": [1, 1], "decomp_temp": 1400,
               "decomp_products": [("Ti", 1), ("S", 2)]},
    "P4S3":   {"formula": "P\u2084S\u2083",   "color": (240, 150, 40), "radius": 28, "mass": 220,
               "atoms": ["P", "P", "P", "P", "S", "S", "S"], "bond_order": [1, 1, 1, 1, 1, 1, 1], "decomp_temp": 1000,
               "decomp_products": [("P", 4), ("S", 3)]},
    "BrO2":   {"formula": "BrO\u2082",       "color": (190, 100, 60), "radius": 21, "mass": 128,
               "atoms": ["Br", "O", "O"], "bond_order": [2, 1], "decomp_temp": 500,
               "decomp_products": [("Br", 1), ("O", 2)]},
    # === New batch 3: Nonmetal halides ===
    "CBr4":   {"formula": "CBr\u2084",      "color": (140, 100, 110), "radius": 28, "mass": 332,
               "atoms": ["C", "Br", "Br", "Br", "Br"], "bond_order": [1, 1, 1, 1], "decomp_temp": 400,
               "decomp_products": [("C", 1), ("Br", 4)]},
    "CI4":    {"formula": "CI\u2084",        "color": (120, 100, 180), "radius": 30, "mass": 530,
               "atoms": ["C", "I", "I", "I", "I"], "bond_order": [1, 1, 1, 1], "decomp_temp": 300,
               "decomp_products": [("C", 1), ("I", 4)]},
    # === New batch 3: Interhalogens ===
    "BrF":    {"formula": "BrF",            "color": (160, 100, 60),  "radius": 18, "mass": 99,
               "atoms": ["Br", "F"], "bond_order": [1], "decomp_temp": 1000,
               "decomp_products": [("Br", 1), ("F", 1)]},
    "IBr":    {"formula": "IBr",             "color": (120, 90, 180), "radius": 22, "mass": 207,
               "atoms": ["I", "Br"], "bond_order": [1], "decomp_temp": 600,
               "decomp_products": [("I", 1), ("Br", 1)]},
    "IF":     {"formula": "IF",              "color": (90, 80, 210),  "radius": 20, "mass": 146,
               "atoms": ["I", "F"], "bond_order": [1], "decomp_temp": 800,
               "decomp_products": [("I", 1), ("F", 1)]},
    # === New batch 3: Alloys ===
    "NaK":    {"formula": "NaK",             "color": (185, 95, 240), "radius": 22, "mass": 62,
               "atoms": ["Na", "K"], "bond_order": [1], "decomp_temp": 500,
               "decomp_products": [("Na", 1), ("K", 1)]},
    "FeTi":   {"formula": "FeTi",            "color": (185, 160, 100), "radius": 22, "mass": 104,
               "atoms": ["Fe", "Ti"], "bond_order": [1], "decomp_temp": 1600,
               "decomp_products": [("Fe", 1), ("Ti", 1)]},
    "CuZn":   {"formula": "CuZn",            "color": (200, 175, 120), "radius": 20, "mass": 129,
               "atoms": ["Cu", "Zn"], "bond_order": [1], "decomp_temp": 1200,
               "decomp_products": [("Cu", 1), ("Zn", 1)]},
    "CuNi":   {"formula": "CuNi",            "color": (195, 170, 105), "radius": 20, "mass": 123,
               "atoms": ["Cu", "Ni"], "bond_order": [1], "decomp_temp": 1300,
               "decomp_products": [("Cu", 1), ("Ni", 1)]},
    "FeCr":   {"formula": "FeCr",            "color": (180, 140, 90), "radius": 20, "mass": 108,
               "atoms": ["Fe", "Cr"], "bond_order": [1], "decomp_temp": 1500,
               "decomp_products": [("Fe", 1), ("Cr", 1)]},
    "MnFe":   {"formula": "MnFe",            "color": (195, 165, 120), "radius": 20, "mass": 111,
               "atoms": ["Mn", "Fe"], "bond_order": [1], "decomp_temp": 1400,
               "decomp_products": [("Mn", 1), ("Fe", 1)]},
    "NiFe":   {"formula": "NiFe",            "color": (175, 200, 120), "radius": 20, "mass": 117,
               "atoms": ["Ni", "Fe"], "bond_order": [1], "decomp_temp": 1500,
               "decomp_products": [("Ni", 1), ("Fe", 1)]},
    "FeNiCr": {"formula": "FeNiCr",          "color": (170, 175, 120), "radius": 23, "mass": 174,
               "atoms": ["Fe", "Ni", "Cr"], "bond_order": [1, 1], "decomp_temp": 1700,
               "decomp_products": [("Fe", 1), ("Ni", 1), ("Cr", 1)]},
    # === New batch 4: Activated placeholder products ===
    "BeCl2":  {"formula": "BeCl\u2082",       "color": (50, 210, 160),  "radius": 20, "mass": 80,
               "atoms": ["Be", "Cl", "Cl"], "bond_order": [1, 1], "decomp_temp": 900,
               "decomp_products": [("Be", 1), ("Cl", 2)]},
    "BF3":    {"formula": "BF\u2083",        "color": (180, 230, 210), "radius": 21, "mass": 68,
               "atoms": ["B", "F", "F", "F"], "bond_order": [1, 1, 1], "decomp_temp": 1200,
               "decomp_products": [("B", 1), ("F", 3)]},
    "NCl3":   {"formula": "NCl\u2083",       "color": (90, 150, 180),  "radius": 24, "mass": 120,
               "atoms": ["N", "Cl", "Cl", "Cl"], "bond_order": [1, 1, 1], "decomp_temp": 300,
               "decomp_products": [("N", 1), ("Cl", 3)]},
    "SBr2":   {"formula": "SBr\u2082",       "color": (220, 200, 50),  "radius": 22, "mass": 192,
               "atoms": ["S", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("S", 1), ("Br", 2)]},
    "AgI":    {"formula": "AgI",             "color": (200, 180, 220), "radius": 23, "mass": 235,
               "atoms": ["Ag", "I"], "bond_order": [1], "decomp_temp": 600,
               "decomp_products": [("Ag", 1), ("I", 1)]},
    "AgBr":   {"formula": "AgBr",            "color": (210, 190, 180), "radius": 22, "mass": 188,
               "atoms": ["Ag", "Br"], "bond_order": [1], "decomp_temp": 700,
               "decomp_products": [("Ag", 1), ("Br", 1)]},
    "BaBr2":  {"formula": "BaBr\u2082",      "color": (120, 230, 130), "radius": 29, "mass": 297,
               "atoms": ["Ba", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 1200,
               "decomp_products": [("Ba", 1), ("Br", 2)]},
    "BaI2":   {"formula": "BaI\u2082",       "color": (110, 220, 140), "radius": 30, "mass": 391,
               "atoms": ["Ba", "I", "I"], "bond_order": [1, 1], "decomp_temp": 1000,
               "decomp_products": [("Ba", 1), ("I", 2)]},
    "AuF3":   {"formula": "AuF\u2083",       "color": (240, 200, 40),  "radius": 24, "mass": 254,
               "atoms": ["Au", "F", "F", "F"], "bond_order": [1, 1, 1], "decomp_temp": 500,
               "decomp_products": [("Au", 1), ("F", 3)]},
    "BaH2":   {"formula": "BaH\u2082",       "color": (130, 240, 130), "radius": 26, "mass": 139,
               "atoms": ["Ba", "H", "H"], "bond_order": [1, 1], "decomp_temp": 500,
               "decomp_products": [("Ba", 1), ("H", 2)]},
    "MnH2":   {"formula": "MnH\u2082",       "color": (190, 175, 130), "radius": 21, "mass": 57,
               "atoms": ["Mn", "H", "H"], "bond_order": [1, 1], "decomp_temp": 400,
               "decomp_products": [("Mn", 1), ("H", 2)]},
    "MgI2":   {"formula": "MgI\u2082",       "color": (100, 190, 100), "radius": 25, "mass": 278,
               "atoms": ["Mg", "I", "I"], "bond_order": [1, 1], "decomp_temp": 1000,
               "decomp_products": [("Mg", 1), ("I", 2)]},
    "CaI2":   {"formula": "CaI\u2082",       "color": (110, 200, 190), "radius": 27, "mass": 294,
               "atoms": ["Ca", "I", "I"], "bond_order": [1, 1], "decomp_temp": 900,
               "decomp_products": [("Ca", 1), ("I", 2)]},
    "CuBr2":  {"formula": "CuBr\u2082",      "color": (220, 160, 80),  "radius": 24, "mass": 223,
               "atoms": ["Cu", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 900,
               "decomp_products": [("Cu", 1), ("Br", 2)]},
    "NiBr2":  {"formula": "NiBr\u2082",      "color": (160, 190, 140), "radius": 24, "mass": 218,
               "atoms": ["Ni", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 1000,
               "decomp_products": [("Ni", 1), ("Br", 2)]},
    "FeBr2":  {"formula": "FeBr\u2082",      "color": (185, 140, 90),  "radius": 24, "mass": 216,
               "atoms": ["Fe", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 900,
               "decomp_products": [("Fe", 1), ("Br", 2)]},
    "TiBr4":  {"formula": "TiBr\u2084",      "color": (180, 185, 210), "radius": 29, "mass": 368,
               "atoms": ["Ti", "Br", "Br", "Br", "Br"], "bond_order": [1, 1, 1, 1], "decomp_temp": 400,
               "decomp_products": [("Ti", 1), ("Br", 4)]},
    "MnBr2":  {"formula": "MnBr\u2082",      "color": (195, 180, 135), "radius": 25, "mass": 214,
               "atoms": ["Mn", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 900,
               "decomp_products": [("Mn", 1), ("Br", 2)]},
    "ZnBr2":  {"formula": "ZnBr\u2082",      "color": (170, 210, 170), "radius": 24, "mass": 225,
               "atoms": ["Zn", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 900,
               "decomp_products": [("Zn", 1), ("Br", 2)]},
    "CuI":    {"formula": "CuI",             "color": (210, 150, 90),  "radius": 22, "mass": 190,
               "atoms": ["Cu", "I"], "bond_order": [1], "decomp_temp": 600,
               "decomp_products": [("Cu", 1), ("I", 1)]},
    "FeI2":   {"formula": "FeI\u2082",       "color": (175, 135, 85),  "radius": 25, "mass": 310,
               "atoms": ["Fe", "I", "I"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("Fe", 1), ("I", 2)]},
    "BeBr2":  {"formula": "BeBr\u2082",      "color": (60, 210, 160),  "radius": 22, "mass": 169,
               "atoms": ["Be", "Br", "Br"], "bond_order": [1, 1], "decomp_temp": 800,
               "decomp_products": [("Be", 1), ("Br", 2)]},
    "NBr3":   {"formula": "NBr\u2083",       "color": (100, 120, 140), "radius": 26, "mass": 254,
               "atoms": ["N", "Br", "Br", "Br"], "bond_order": [1, 1, 1], "decomp_temp": 200,
               "decomp_products": [("N", 1), ("Br", 3)]},
    "CrBr3":  {"formula": "CrBr\u2083",      "color": (140, 150, 190), "radius": 27, "mass": 292,
               "atoms": ["Cr", "Br", "Br", "Br"], "bond_order": [1, 1, 1], "decomp_temp": 800,
               "decomp_products": [("Cr", 1), ("Br", 3)]},
    "BeI2":   {"formula": "BeI\u2082",       "color": (70, 200, 160),  "radius": 24, "mass": 263,
               "atoms": ["Be", "I", "I"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("Be", 1), ("I", 2)]},
    "NiI2":   {"formula": "NiI\u2082",       "color": (150, 185, 130), "radius": 25, "mass": 312,
               "atoms": ["Ni", "I", "I"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("Ni", 1), ("I", 2)]},
    "ZnI2":   {"formula": "ZnI\u2082",       "color": (160, 200, 160), "radius": 25, "mass": 319,
               "atoms": ["Zn", "I", "I"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("Zn", 1), ("I", 2)]},
    # === New batch 4: Extra compounds ===
    "Na2O2":  {"formula": "Na\u2082O\u2082", "color": (200, 100, 240), "radius": 25, "mass": 78,
               "atoms": ["Na", "Na", "O", "O"], "bond_order": [1, 1, 1], "decomp_temp": 800,
               "decomp_products": [("Na", 2), ("O", 2)]},
    "KO2":    {"formula": "KO\u2082",        "color": (210, 140, 235), "radius": 26, "mass": 71,
               "atoms": ["K", "O", "O"], "bond_order": [1, 1], "decomp_temp": 700,
               "decomp_products": [("K", 1), ("O", 2)]},
    "Li2O2":  {"formula": "Li\u2082O\u2082", "color": (240, 100, 100), "radius": 23, "mass": 46,
               "atoms": ["Li", "Li", "O", "O"], "bond_order": [1, 1, 1], "decomp_temp": 700,
               "decomp_products": [("Li", 2), ("O", 2)]},
    "H2SO4":  {"formula": "H\u2082SO\u2084", "color": (200, 190, 70), "radius": 27, "mass": 98,
               "atoms": ["H", "H", "S", "O", "O", "O", "O"], "bond_order": [1, 1, 2, 2, 1, 1], "decomp_temp": 600,
               "decomp_products": [("H", 2), ("S", 1), ("O", 4)]},
    "BaS":    {"formula": "BaS",            "color": (120, 255, 130), "radius": 26, "mass": 169,
               "atoms": ["Ba", "S"], "bond_order": [2], "decomp_temp": 1800,
               "decomp_products": [("Ba", 1), ("S", 1)]},
    "H3PO4":  {"formula": "H\u2083PO\u2084", "color": (230, 150, 40),  "radius": 28, "mass": 98,
               "atoms": ["H", "H", "H", "P", "O", "O", "O", "O"], "bond_order": [1, 1, 1, 2, 2, 1, 1], "decomp_temp": 500,
               "decomp_products": [("H", 3), ("P", 1), ("O", 4)]},
}

# ─── Reaction Definitions ────────────────────────────────────────────────────
REACTIONS = {
    # === Original reactions ===
    ("H", "H"):    {"products": [("H2", 1)],       "energy": -436,  "equation": "2H \u2192 H\u2082"},
    ("H", "O"):    {"products": [("H2O", 1)],      "energy": -572,  "equation": "2H\u2082 + O\u2082 \u2192 2H\u2082O",
                    "min_reactants": {"H": 2, "O": 1}},
    ("H", "Cl"):   {"products": [("HCl", 1)],      "energy": -92,   "equation": "H\u2082 + Cl\u2082 \u2192 2HCl",
                    "min_reactants": {"H": 1, "Cl": 1}},
    ("H", "F"):    {"products": [("HF", 1)],       "energy": -569,  "equation": "H\u2082 + F\u2082 \u2192 2HF",
                    "min_reactants": {"H": 1, "F": 1}},
    ("H", "N"):    {"products": [("NH3", 1)],      "energy": -92,   "equation": "N\u2082 + 3H\u2082 \u2192 2NH\u2083",
                    "min_reactants": {"H": 3, "N": 1}},
    ("H", "S"):    {"products": [("H2S", 1)],      "energy": -20,   "equation": "H\u2082 + S \u2192 H\u2082S",
                    "min_reactants": {"H": 2, "S": 1}},
    ("Na", "Cl"):  {"products": [("NaCl", 1)],     "energy": -411,  "equation": "Na + Cl \u2192 NaCl"},
    ("Na", "O"):   {"products": [("NaOH", 1)],     "energy": -425,  "equation": "2Na + 2H\u2082O \u2192 2NaOH + H\u2082",
                    "min_reactants": {"Na": 1, "O": 1, "H": 1}},
    ("C", "O"):    {"products": [("CO2", 1)],      "energy": -393,  "equation": "C + O\u2082 \u2192 CO\u2082",
                    "min_reactants": {"C": 1, "O": 2}},
    ("C", "H"):    {"products": [("CH4", 1)],      "energy": -75,   "equation": "C + 2H\u2082 \u2192 CH\u2084",
                    "min_reactants": {"C": 1, "H": 4}},
    ("N", "O"):    {"products": [("NO2", 1)],      "energy": 33,    "equation": "N\u2082 + 2O\u2082 \u2192 2NO\u2082",
                    "min_reactants": {"N": 1, "O": 2}},
    ("O", "O"):    {"products": [("O2", 1)],       "energy": -498,  "equation": "O + O \u2192 O\u2082"},
    ("N", "N"):    {"products": [("N2", 1)],       "energy": -945,  "equation": "N + N \u2192 N\u2082"},
    ("S", "O"):    {"products": [("SO2", 1)],      "energy": -297,  "equation": "S + O\u2082 \u2192 SO\u2082",
                    "min_reactants": {"S": 1, "O": 2}},
    ("Fe", "O"):   {"products": [("FeO", 1)],      "energy": -272,  "equation": "2Fe + O\u2082 \u2192 2FeO",
                    "min_reactants": {"Fe": 1, "O": 1}},
    ("Ca", "O"):   {"products": [("CaO", 1)],      "energy": -635,  "equation": "2Ca + O\u2082 \u2192 2CaO",
                    "min_reactants": {"Ca": 1, "O": 1}},
    ("Ca", "C"):   {"products": [("CaCO3", 1)],    "energy": -1207, "equation": "CaO + CO\u2082 \u2192 CaCO\u2083",
                    "min_reactants": {"Ca": 1, "C": 1, "O": 3}},
    ("C", "O"):    {"products": [("CO", 1)],       "energy": -111,  "equation": "2C + O\u2082 \u2192 2CO",
                    "min_reactants": {"C": 1, "O": 1}, "alt": True},
    # === New: Lithium ===
    ("Li", "F"):   {"products": [("LiF", 1)],      "energy": -617,  "equation": "Li + F \u2192 LiF"},
    ("Li", "Cl"):  {"products": [("LiCl", 1)],     "energy": -409,  "equation": "Li + Cl \u2192 LiCl"},
    ("Li", "O"):   {"products": [("LiOH", 1)],     "energy": -487,  "equation": "2Li + 2H\u2082O \u2192 2LiOH + H\u2082",
                    "min_reactants": {"Li": 1, "O": 1, "H": 1}},
    ("Li", "H"):   {"products": [("Li2O", 1)],     "energy": -599,  "equation": "4Li + O\u2082 \u2192 2Li\u2082O",
                    "min_reactants": {"Li": 2, "O": 1}},
    # === New: Beryllium ===
    ("Be", "O"):   {"products": [("BeO", 1)],      "energy": -610,  "equation": "2Be + O\u2082 \u2192 2BeO",
                    "min_reactants": {"Be": 1, "O": 1}},
    ("Be", "Cl"):   {"products": [("BeCl2", 1)],    "energy": -468,  "equation": "Be + Cl\u2082 \u2192 BeCl\u2082",
                    "min_reactants": {"Be": 1, "Cl": 2}},
    # === New: Magnesium ===
    ("Mg", "O"):   {"products": [("MgO", 1)],      "energy": -602,  "equation": "2Mg + O\u2082 \u2192 2MgO",
                    "min_reactants": {"Mg": 1, "O": 1}},
    ("Mg", "Cl"):  {"products": [("MgCl2", 1)],    "energy": -641,  "equation": "Mg + Cl\u2082 \u2192 MgCl\u2082",
                    "min_reactants": {"Mg": 1, "Cl": 2}},
    ("Mg", "S"):   {"products": [("MgS", 1)],      "energy": -347,  "equation": "Mg + S \u2192 MgS"},
    # === New: Potassium ===
    ("K", "Cl"):   {"products": [("KCl", 1)],      "energy": -437,  "equation": "K + Cl \u2192 KCl"},
    ("K", "O"):   {"products": [("KOH", 1)],      "energy": -393,  "equation": "2K + 2H\u2082O \u2192 2KOH + H\u2082",
                    "min_reactants": {"K": 1, "O": 1, "H": 1}},
    ("K", "H"):   {"products": [("K2O", 1)],      "energy": -363,  "equation": "4K + O\u2082 \u2192 2K\u2082O",
                    "min_reactants": {"K": 2, "O": 1}},
    # === New: Barium ===
    ("Ba", "O"):   {"products": [("BaO", 1)],      "energy": -553,  "equation": "2Ba + O\u2082 \u2192 2BaO",
                    "min_reactants": {"Ba": 1, "O": 1}},
    ("Ba", "S"):   {"products": [("BaO", 1)],      "energy": -460,  "equation": "Ba + S + O\u2082 \u2192 BaSO\u2084",
                    "min_reactants": {"Ba": 1, "S": 1, "O": 2}},
    # === New: Silicon ===
    ("Si", "O"):   {"products": [("SiO2", 1)],     "energy": -911,  "equation": "Si + O\u2082 \u2192 SiO\u2082",
                    "min_reactants": {"Si": 1, "O": 2}},
    ("Si", "H"):   {"products": [("SiH4", 1)],     "energy": 34,    "equation": "Si + 2H\u2082 \u2192 SiH\u2084",
                    "min_reactants": {"Si": 1, "H": 4}},
    # === New: Phosphorus ===
    ("P", "H"):    {"products": [("PH3", 1)],      "energy": 5,     "equation": "P + 1.5H\u2082 \u2192 PH\u2083",
                    "min_reactants": {"P": 1, "H": 3}},
    ("P", "O"):    {"products": [("P2O5", 1)],     "energy": 0,     "equation": "(needs catalyst)", "min_reactants": {}},
    # === New: Boron ===
    ("B", "F"):   {"products": [("BF3", 1)],      "energy": -1137, "equation": "2B + 3F\u2082 \u2192 2BF\u2083",
                    "min_reactants": {"B": 1, "F": 3}},
    ("B", "O"):    {"products": [],               "energy": 0,     "equation": "(B\u2082O\u2083 needs catalyst)", "min_reactants": {}},
    # === New: Halogen diatomics ===
    ("Br", "Br"):  {"products": [("Br2", 1)],     "energy": -193,  "equation": "2Br \u2192 Br\u2082"},
    ("I", "I"):    {"products": [("I2", 1)],      "energy": -151,  "equation": "2I \u2192 I\u2082"},
    ("H", "Br"):   {"products": [("HBr", 1)],      "energy": -36,   "equation": "H\u2082 + Br\u2082 \u2192 2HBr",
                    "min_reactants": {"H": 1, "Br": 1}},
    ("H", "I"):    {"products": [("HI", 1)],       "energy": 26,    "equation": "H\u2082 + I\u2082 \u2192 2HI",
                    "min_reactants": {"H": 1, "I": 1}},
    # === New: Transition metal oxides ===
    ("Ti", "O"):   {"products": [("TiO2", 1)],     "energy": -944,  "equation": "Ti + O\u2082 \u2192 TiO\u2082",
                    "min_reactants": {"Ti": 1, "O": 2}},
    ("Cr", "O"):   {"products": [("Cr2O3", 1)],    "energy": -1140, "equation": "4Cr + 3O\u2082 \u2192 2Cr\u2082O\u2083",
                    "min_reactants": {"Cr": 2, "O": 3}},
    ("Mn", "O"):   {"products": [("MnO2", 1)],     "energy": -520,  "equation": "Mn + O\u2082 \u2192 MnO\u2082",
                    "min_reactants": {"Mn": 1, "O": 2}},
    ("Ni", "O"):   {"products": [("NiO", 1)],      "energy": -240,  "equation": "2Ni + O\u2082 \u2192 2NiO",
                    "min_reactants": {"Ni": 1, "O": 1}},
    ("Cu", "O"):   {"products": [("CuO", 1)],      "energy": -157,  "equation": "2Cu + O\u2082 \u2192 2CuO",
                    "min_reactants": {"Cu": 1, "O": 1}},
    ("Cu", "Cl"):  {"products": [("CuCl2", 1)],    "energy": -219,  "equation": "Cu + Cl\u2082 \u2192 CuCl\u2082",
                    "min_reactants": {"Cu": 1, "Cl": 2}},
    ("Zn", "O"):   {"products": [("ZnO", 1)],      "energy": -350,  "equation": "2Zn + O\u2082 \u2192 2ZnO",
                    "min_reactants": {"Zn": 1, "O": 1}},
    ("Zn", "Cl"):  {"products": [("ZnCl2", 1)],    "energy": -416,  "equation": "Zn + Cl\u2082 \u2192 ZnCl\u2082",
                    "min_reactants": {"Zn": 1, "Cl": 2}},
    ("Zn", "S"):   {"products": [("ZnS", 1)],      "energy": -206,  "equation": "Zn + S \u2192 ZnS"},
    # === New: Silver & Gold ===
    ("Ag", "Cl"):  {"products": [("AgCl", 1)],     "energy": -127,  "equation": "Ag + Cl \u2192 AgCl"},
    ("Ag", "O"):   {"products": [("Ag2O", 1)],     "energy": -31,   "equation": "4Ag + O\u2082 \u2192 2Ag\u2082O",
                    "min_reactants": {"Ag": 2, "O": 1}},
    # === New: Additional reactions for existing elements ===
    ("Na", "F"):   {"products": [("NaF", 1)],      "energy": -571,  "equation": "Na + F \u2192 NaF"},
    ("Na", "S"):   {"products": [("Na2S", 1)],     "energy": -364,  "equation": "2Na + S \u2192 Na\u2082S",
                    "min_reactants": {"Na": 2, "S": 1}},
    ("Ca", "Cl"):  {"products": [("CaCl2", 1)],    "energy": -796,  "equation": "Ca + Cl\u2082 \u2192 CaCl\u2082",
                    "min_reactants": {"Ca": 1, "Cl": 2}},
    ("Ca", "S"):   {"products": [("CaS", 1)],      "energy": -482,  "equation": "Ca + S \u2192 CaS"},
    ("Fe", "S"):   {"products": [("FeS", 1)],      "energy": -100,  "equation": "Fe + S \u2192 FeS"},
    ("Fe", "Cl"):  {"products": [("FeCl3", 1)],    "energy": -405,  "equation": "2Fe + 3Cl\u2082 \u2192 2FeCl\u2083",
                    "min_reactants": {"Fe": 1, "Cl": 3}},
    ("Fe", "Fe"):  {"products": [("Fe2O3", 1)],    "energy": -824,  "equation": "4Fe + 3O\u2082 \u2192 2Fe\u2082O\u2083",
                    "min_reactants": {"Fe": 2, "O": 3}},
    ("H", "C"):    {"products": [("HNO3", 1)],     "energy": -207,  "equation": "requires N+O too", "min_reactants": {}},
    # ========================================================================
    # === NEW REACTIONS BATCH 2: 80+ additional reaction pathways ===
    # ========================================================================
    # --- Interhalogens ---
    ("Cl", "F"):   {"products": [("ClF", 1)],      "energy": -51,   "equation": "Cl\\u2082 + F\\u2082 \\u2192 2ClF",
                    "min_reactants": {"Cl": 1, "F": 1}},
    ("Br", "Cl"):  {"products": [("BrCl", 1)],     "energy": -30,   "equation": "Br\\u2082 + Cl\\u2082 \\u2192 2BrCl",
                    "min_reactants": {"Br": 1, "Cl": 1}},
    ("Br", "F"):   {"products": [("BrF", 1)],      "energy": -60,   "equation": "Br\\u2082 + F\\u2082 \\u2192 2BrF",
                    "min_reactants": {"Br": 1, "F": 1}},
    ("I", "Cl"):   {"products": [("ICl", 1)],      "energy": -18,   "equation": "I\\u2082 + Cl\\u2082 \\u2192 2ICl",
                    "min_reactants": {"I": 1, "Cl": 1}},
    ("I", "F"):    {"products": [("IF", 1)],       "energy": -40,   "equation": "I\\u2082 + F\\u2082 \\u2192 2IF",
                    "min_reactants": {"I": 1, "F": 1}},
    ("I", "Br"):   {"products": [("IBr", 1)],      "energy": -10,   "equation": "I\\u2082 + Br\\u2082 \\u2192 2IBr",
                    "min_reactants": {"I": 1, "Br": 1}},
    # --- Alkali bromides/iodides ---
    ("Li", "Br"):  {"products": [("LiBr", 1)],     "energy": -350,  "equation": "Li + Br \\u2192 LiBr"},
    ("Li", "I"):   {"products": [("LiI", 1)],      "energy": -270,  "equation": "Li + I \\u2192 LiI"},
    ("Na", "Br"):  {"products": [("NaBr", 1)],     "energy": -361,  "equation": "Na + Br \\u2192 NaBr"},
    ("Na", "I"):   {"products": [("NaI", 1)],      "energy": -287,  "equation": "Na + I \\u2192 NaI"},
    ("K", "Br"):   {"products": [("KBr", 1)],      "energy": -392,  "equation": "K + Br \\u2192 KBr"},
    ("K", "I"):    {"products": [("KI", 1)],       "energy": -328,  "equation": "K + I \\u2192 KI"},
    # --- Alkali sulfides ---
    ("Li", "S"):   {"products": [("Li2S", 1)],     "energy": -440,  "equation": "2Li + S \\u2192 Li\\u2082S",
                    "min_reactants": {"Li": 2, "S": 1}},
    ("K", "S"):    {"products": [("K2S", 1)],      "energy": -430,  "equation": "2K + S \\u2192 K\\u2082S",
                    "min_reactants": {"K": 2, "S": 1}},
    # --- Alkali fluorides ---
    ("Li", "F"):   {"products": [("LiF", 1)],      "energy": -617,  "equation": "Li + F \\u2192 LiF"},
    ("K", "F"):    {"products": [("KF", 1)],       "energy": -568,  "equation": "K + F \\u2192 KF"},
    # --- Alkali nitrides ---
    ("Li", "N"):   {"products": [("Li3N", 1)],     "energy": -165,  "equation": "6Li + N\\u2082 \\u2192 2Li\\u2083N",
                    "min_reactants": {"Li": 3, "N": 1}},
    # --- Beryllium compounds ---
    ("Be", "F"):   {"products": [("BeF2", 1)],     "energy": -1025, "equation": "Be + F\\u2082 \\u2192 BeF\\u2082",
                    "min_reactants": {"Be": 1, "F": 2}},
    ("Be", "S"):   {"products": [("BeS", 1)],      "energy": -234,  "equation": "Be + S \\u2192 BeS"},
    # --- Magnesium fluoride/bromide/nitride ---
    ("Mg", "F"):   {"products": [("MgF2", 1)],     "energy": -1122, "equation": "Mg + F\\u2082 \\u2192 MgF\\u2082",
                    "min_reactants": {"Mg": 1, "F": 2}},
    ("Mg", "Br"):  {"products": [("MgBr2", 1)],    "energy": -524,  "equation": "Mg + Br\\u2082 \\u2192 MgBr\\u2082",
                    "min_reactants": {"Mg": 1, "Br": 2}},
    ("Mg", "N"):   {"products": [("Mg3N2", 1)],    "energy": -461,  "equation": "3Mg + N\\u2082 \\u2192 Mg\\u2083N\\u2082",
                    "min_reactants": {"Mg": 3, "N": 1}},
    # --- Barium halides ---
    ("Ba", "Cl"):  {"products": [("BaCl2", 1)],    "energy": -860,  "equation": "Ba + Cl\\u2082 \\u2192 BaCl\\u2082",
                    "min_reactants": {"Ba": 1, "Cl": 2}},
    ("Ba", "F"):   {"products": [("BaF2", 1)],     "energy": -1200, "equation": "Ba + F\\u2082 \\u2192 BaF\\u2082",
                    "min_reactants": {"Ba": 1, "F": 2}},
    ("Ba", "Br"):   {"products": [("BaBr2", 1)],    "energy": -760,  "equation": "Ba + Br\u2082 \u2192 BaBr\u2082",
                    "min_reactants": {"Ba": 1, "Br": 2}},
    # --- Calcium fluoride/bromide ---
    ("Ca", "F"):   {"products": [("CaF2", 1)],     "energy": -1228, "equation": "Ca + F\\u2082 \\u2192 CaF\\u2082",
                    "min_reactants": {"Ca": 1, "F": 2}},
    ("Ca", "Br"):  {"products": [("CaBr2", 1)],    "energy": -675,  "equation": "Ca + Br\\u2082 \\u2192 CaBr\\u2082",
                    "min_reactants": {"Ca": 1, "Br": 2}},
    # --- Silicon compounds ---
    ("Si", "Cl"):  {"products": [("SiCl4", 1)],    "energy": -657,  "equation": "Si + 2Cl\\u2082 \\u2192 SiCl\\u2084",
                    "min_reactants": {"Si": 1, "Cl": 4}},
    ("Si", "F"):   {"products": [("SiF4", 1)],     "energy": -1615, "equation": "Si + 2F\\u2082 \\u2192 SiF\\u2084",
                    "min_reactants": {"Si": 1, "F": 4}},
    ("Si", "C"):   {"products": [("SiC", 1)],      "energy": -65,   "equation": "Si + C \\u2192 SiC"},
    ("Si", "N"):   {"products": [],               "energy": -745,  "equation": "(Si\\u2083N\\u2084 needs 4N)", "min_reactants": {}},
    # --- Phosphorus halides ---
    ("P", "Cl"):   {"products": [("PCl3", 1)],     "energy": -319,  "equation": "P + 1.5Cl\\u2082 \\u2192 PCl\\u2083",
                    "min_reactants": {"P": 1, "Cl": 3}},
    ("P", "F"):    {"products": [("PF3", 1)],      "energy": -910,  "equation": "P + 1.5F\\u2082 \\u2192 PF\\u2083",
                    "min_reactants": {"P": 1, "F": 3}},
    ("P", "S"):    {"products": [],               "energy": 0,     "equation": "(P\\u2084S\\u2083 needs catalyst)", "min_reactants": {}},
    # --- Boron compounds ---
    ("B", "Cl"):   {"products": [("BCl3", 1)],     "energy": -427,  "equation": "B + 1.5Cl\\u2082 \\u2192 BCl\\u2083",
                    "min_reactants": {"B": 1, "Cl": 3}},
    ("B", "N"):    {"products": [("BN", 1)],       "energy": -257,  "equation": "B + N \\u2192 BN (boron nitride)"},
    # --- Titanium halides/nitride ---
    ("Ti", "Cl"):  {"products": [("TiCl4", 1)],    "energy": -763,  "equation": "Ti + 2Cl\\u2082 \\u2192 TiCl\\u2084",
                    "min_reactants": {"Ti": 1, "Cl": 4}},
    ("Ti", "F"):   {"products": [("TiF4", 1)],     "energy": -1648, "equation": "Ti + 2F\\u2082 \\u2192 TiF\\u2084",
                    "min_reactants": {"Ti": 1, "F": 4}},
    ("Ti", "N"):   {"products": [("TiN", 1)],      "energy": -338,  "equation": "2Ti + N\\u2082 \\u2192 2TiN",
                    "min_reactants": {"Ti": 1, "N": 1}},
    # --- Chromium halides/sulfide ---
    ("Cr", "Cl"):  {"products": [("CrCl3", 1)],    "energy": -556,  "equation": "2Cr + 3Cl\\u2082 \\u2192 2CrCl\\u2083",
                    "min_reactants": {"Cr": 1, "Cl": 3}},
    ("Cr", "F"):   {"products": [("CrF3", 1)],     "energy": -1160, "equation": "2Cr + 3F\\u2082 \\u2192 2CrF\\u2083",
                    "min_reactants": {"Cr": 1, "F": 3}},
    ("Cr", "S"):   {"products": [("Cr2S3", 1)],    "energy": -460,  "equation": "2Cr + 3S \\u2192 Cr\\u2082S\\u2083",
                    "min_reactants": {"Cr": 2, "S": 3}},
    # --- Manganese halides/sulfide ---
    ("Mn", "Cl"):  {"products": [("MnCl2", 1)],    "energy": -401,  "equation": "Mn + Cl\\u2082 \\u2192 MnCl\\u2082",
                    "min_reactants": {"Mn": 1, "Cl": 2}},
    ("Mn", "F"):   {"products": [("MnF2", 1)],     "energy": -792,  "equation": "Mn + F\\u2082 \\u2192 MnF\\u2082",
                    "min_reactants": {"Mn": 1, "F": 2}},
    ("Mn", "S"):   {"products": [("MnS", 1)],      "energy": -214,  "equation": "Mn + S \\u2192 MnS"},
    # --- Nickel halides/sulfide ---
    ("Ni", "Cl"):  {"products": [("NiCl2", 1)],    "energy": -305,  "equation": "Ni + Cl\\u2082 \\u2192 NiCl\\u2082",
                    "min_reactants": {"Ni": 1, "Cl": 2}},
    ("Ni", "F"):   {"products": [("NiF2", 1)],     "energy": -607,  "equation": "Ni + F\\u2082 \\u2192 NiF\\u2082",
                    "min_reactants": {"Ni": 1, "F": 2}},
    ("Ni", "S"):   {"products": [("NiS", 1)],      "energy": -82,   "equation": "Ni + S \\u2192 NiS"},
    # --- Copper halide/fluoride/sulfide ---
    ("Cu", "F"):   {"products": [("CuF2", 1)],     "energy": -531,  "equation": "Cu + F\\u2082 \\u2192 CuF\\u2082",
                    "min_reactants": {"Cu": 1, "F": 2}},
    ("Cu", "S"):   {"products": [("CuS", 1)],      "energy": -53,   "equation": "Cu + S \\u2192 CuS"},
    # --- Zinc fluoride ---
    ("Zn", "F"):   {"products": [("ZnF2", 1)],     "energy": -764,  "equation": "Zn + F\\u2082 \\u2192 ZnF\\u2082",
                    "min_reactants": {"Zn": 1, "F": 2}},
    # --- Silver sulfide/fluoride ---
    ("Ag", "S"):   {"products": [("Ag2S", 1)],     "energy": -32,   "equation": "4Ag + 2H\\u2082S + O\\u2082 \\u2192 2Ag\\u2082S + 2H\\u2082O",
                    "min_reactants": {"Ag": 2, "S": 1}},
    ("Ag", "F"):   {"products": [("AgF", 1)],      "energy": -205,  "equation": "Ag + F \\u2192 AgF"},
    # --- Gold chloride ---
    ("Au", "Cl"):  {"products": [("AuCl3", 1)],    "energy": -118,  "equation": "2Au + 3Cl\\u2082 \\u2192 2AuCl\\u2083",
                    "min_reactants": {"Au": 1, "Cl": 3}},
    ("Au", "F"):   {"products": [("AuF3", 1)],     "energy": -350,  "equation": "2Au + 3F\u2082 \u2192 2AuF\u2083",
                    "min_reactants": {"Au": 1, "F": 3}},
    # --- Iron fluoride ---
    ("Fe", "F"):   {"products": [("FeF3", 1)],     "energy": -1040, "equation": "2Fe + 3F\\u2082 \\u2192 2FeF\\u2083",
                    "min_reactants": {"Fe": 1, "F": 3}},
    # --- Nonmetal halides ---
    ("C", "Cl"):   {"products": [("CCl4", 1)],     "energy": -95,   "equation": "C + 2Cl\\u2082 \\u2192 CCl\\u2084",
                    "min_reactants": {"C": 1, "Cl": 4}},
    ("C", "F"):    {"products": [("CF4", 1)],      "energy": -680,  "equation": "C + 2F\\u2082 \\u2192 CF\\u2084",
                    "min_reactants": {"C": 1, "F": 4}},
    ("C", "S"):    {"products": [("CS2", 1)],      "energy": 89,    "equation": "C + 2S \\u2192 CS\\u2082 (endothermic)",
                    "min_reactants": {"C": 1, "S": 2}},
    ("N", "F"):    {"products": [("NF3", 1)],      "energy": -132,  "equation": "N\\u2082 + 3F\\u2082 \\u2192 2NF\\u2083",
                    "min_reactants": {"N": 1, "F": 3}},
    ("N", "Cl"):   {"products": [("NCl3", 1)],     "energy": 230,   "equation": "N\u2082 + 3Cl\u2082 \u2192 2NCl\u2083 (endothermic)",
                    "min_reactants": {"N": 1, "Cl": 3}},
    ("S", "F"):    {"products": [("SF2", 1)],      "energy": -283,  "equation": "S + F\\u2082 \\u2192 SF\\u2082",
                    "min_reactants": {"S": 1, "F": 2}},
    ("S", "Cl"):   {"products": [("SCl2", 1)],     "energy": -60,   "equation": "S + Cl\\u2082 \\u2192 SCl\\u2082",
                    "min_reactants": {"S": 1, "Cl": 2}},
    # --- Cross-metal and exotic ---
    ("Cu", "N"):   {"products": [],               "energy": 0,     "equation": "(Cu\\u2083N unstable)", "min_reactants": {}},
    ("Fe", "N"):   {"products": [],               "energy": -11,   "equation": "(Fe\\u2084N needs catalyst)", "min_reactants": {}},
    ("Na", "N"):   {"products": [],               "energy": 0,     "equation": "(NaN\\u2083 needs 3N)", "min_reactants": {}},
    ("K", "N"):    {"products": [],               "energy": 0,     "equation": "(K\\u2083N unstable)", "min_reactants": {}},
    # --- Carbon-nitrogen (cyanide route, simplified) ---
    ("C", "N"):    {"products": [],               "energy": 0,     "equation": "(CN compounds need catalyst)", "min_reactants": {}},
    # ========================================================================
    # === NEW REACTIONS BATCH 3: 110+ additional reaction pathways ===
    # ========================================================================
    # --- Metal hydrides ---
    ("Na", "H"):   {"products": [("NaH", 1)],      "energy": -56,   "equation": "Na + H \\u2192 NaH"},
    ("K", "H"):    {"products": [("KH", 1)],       "energy": -58,   "equation": "K + H \\u2192 KH"},
    ("Li", "H"):   {"products": [("LiH", 1)],      "energy": -90,   "equation": "Li + H \\u2192 LiH"},
    ("Mg", "H"):  {"products": [("MgH2", 1)],     "energy": -75,   "equation": "Mg + H\\u2082 \\u2192 MgH\\u2082",
                    "min_reactants": {"Mg": 1, "H": 2}},
    ("Ca", "H"):   {"products": [("CaH2", 1)],     "energy": -186,  "equation": "Ca + H\\u2082 \\u2192 CaH\\u2082",
                    "min_reactants": {"Ca": 1, "H": 2}},
    ("Ti", "H"):   {"products": [("TiH2", 1)],     "energy": -144,  "equation": "Ti + H\\u2082 \\u2192 TiH\\u2082",
                    "min_reactants": {"Ti": 1, "H": 2}},
    ("Mn", "H"):   {"products": [("MnH2", 1)],     "energy": -75,   "equation": "Mn + H\u2082 \u2192 MnH\u2082",
                    "min_reactants": {"Mn": 1, "H": 2}},
    ("Ni", "H"):   {"products": [],               "energy": 0,     "equation": "(NiH unstable)", "min_reactants": {}},
    ("Zn", "H"):   {"products": [],               "energy": 0,     "equation": "(ZnH\\u2082 unstable)", "min_reactants": {}},
    ("Fe", "H"):   {"products": [],               "energy": 0,     "equation": "(FeH needs catalyst)", "min_reactants": {}},
    ("Cu", "H"):   {"products": [],               "energy": 0,     "equation": "(CuH unstable)", "min_reactants": {}},
    # --- Sodium oxide ---
    ("Na", "Na"):  {"products": [("Na2O", 1)],     "energy": -416,  "equation": "4Na + O\\u2082 \\u2192 2Na\\u2082O",
                    "min_reactants": {"Na": 2, "O": 1}},
    # --- Oxygen with halogens ---
    ("F", "O"):    {"products": [("OF2", 1)],      "energy": 25,    "equation": "F\\u2082 + O\\u2082 \\u2192 2OF\\u2082 (endothermic)",
                    "min_reactants": {"F": 1, "O": 1}},
    ("Cl", "O"):  {"products": [("ClO2", 1)],     "energy": 30,    "equation": "Cl\\u2082 + O\\u2082 \\u2192 2ClO\\u2082 (endothermic)",
                    "min_reactants": {"Cl": 1, "O": 1}},
    ("Br", "O"):   {"products": [("BrO2", 1)],     "energy": 30,    "equation": "Br\\u2082 + O\\u2082 \\u2192 2BrO\\u2082 (endothermic)",
                    "min_reactants": {"Br": 1, "O": 1}},
    ("I", "O"):    {"products": [],               "energy": 0,     "equation": "(I\\u2082O\\u2085 needs 5O)", "min_reactants": {}},
    # --- Boron oxide ---
    ("B", "O"):    {"products": [("B2O3", 1)],     "energy": -1273, "equation": "4B + 3O\\u2082 \\u2192 2B\\u2082O\\u2083",
                    "min_reactants": {"B": 2, "O": 3}},
    # --- Phosphorus pentoxide ---
    ("P", "O"):    {"products": [("P2O5", 1)],     "energy": -2984, "equation": "4P + 5O\\u2082 \\u2192 2P\\u2082O\\u2085",
                    "min_reactants": {"P": 2, "O": 5}},
    # --- Carbon with remaining elements ---
    ("C", "Br"):   {"products": [("CBr4", 1)],     "energy": 30,    "equation": "C + 2Br\\u2082 \\u2192 CBr\\u2084 (endothermic)",
                    "min_reactants": {"C": 1, "Br": 4}},
    ("C", "I"):    {"products": [("CI4", 1)],      "energy": 60,    "equation": "C + 2I\\u2082 \\u2192 CI\\u2084 (endothermic)",
                    "min_reactants": {"C": 1, "I": 4}},
    ("C", "Ti"):   {"products": [("TiC", 1)],      "energy": -184,  "equation": "Ti + C \\u2192 TiC"},
    ("C", "Cr"):   {"products": [("Cr3C2", 1)],    "energy": -90,   "equation": "3Cr + 2C \\u2192 Cr\\u2083C\\u2082",
                    "min_reactants": {"Cr": 3, "C": 2}},
    ("C", "Mn"):   {"products": [],               "energy": 0,     "equation": "(Mn\\u2083C needs 3Mn + C)", "min_reactants": {}},
    ("C", "Fe"):   {"products": [("Fe3C", 1)],     "energy": -25,   "equation": "3Fe + C \\u2192 Fe\\u2083C (cementite)",
                    "min_reactants": {"Fe": 3, "C": 1}},
    ("C", "B"):    {"products": [("B4C", 1)],      "energy": -71,   "equation": "4B + C \\u2192 B\\u2084C (boron carbide)",
                    "min_reactants": {"B": 4, "C": 1}},
    ("C", "Ca"):   {"products": [("CaC2", 1)],     "energy": -60,   "equation": "Ca + 2C \\u2192 CaC\\u2082 (carbide)",
                    "min_reactants": {"Ca": 1, "C": 2}},
    ("C", "Mg"):   {"products": [],               "energy": 0,     "equation": "(Mg\\u2082C\\u2083 needs catalyst)", "min_reactants": {}},
    ("C", "Si"):   {"products": [("SiC2", 1)],     "energy": 150,   "equation": "2C + Si \\u2192 SiC\\u2082 (endothermic)",
                    "min_reactants": {"C": 2, "Si": 1}},
    ("C", "Li"):   {"products": [],               "energy": 0,     "equation": "(Li\\u2082C\\u2082 needs 2Li)", "min_reactants": {}},
    ("C", "K"):    {"products": [],               "energy": 0,     "equation": "(KC\\u2084 unstable)", "min_reactants": {}},
    ("C", "Na"):   {"products": [],               "energy": 0,     "equation": "(Na\\u2082C\\u2082 needs 2Na)", "min_reactants": {}},
    ("C", "Ni"):   {"products": [],               "energy": 0,     "equation": "(no stable nickel carbide)", "min_reactants": {}},
    ("C", "Cu"):   {"products": [],               "energy": 0,     "equation": "(no stable copper carbide)", "min_reactants": {}},
    ("C", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable zinc carbide)", "min_reactants": {}},
    ("C", "P"):    {"products": [],               "energy": 0,     "equation": "(phosphorus carbide needs catalyst)", "min_reactants": {}},
    # --- Sulfur with remaining elements ---
    ("S", "S"):    {"products": [("S8", 1)],       "energy": -223,  "equation": "8S \\u2192 S\\u2088"},
    ("S", "Si"):   {"products": [("SiS2", 1)],     "energy": 143,   "equation": "Si + 2S \\u2192 SiS\\u2082 (endothermic)",
                    "min_reactants": {"Si": 1, "S": 2}},
    ("S", "Ti"):   {"products": [("TiS2", 1)],     "energy": -223,  "equation": "Ti + 2S \\u2192 TiS\\u2082",
                    "min_reactants": {"Ti": 1, "S": 2}},
    ("S", "P"):    {"products": [("P4S3", 1)],     "energy": -154,  "equation": "4P + 3S \\u2192 P\\u2084S\\u2083",
                    "min_reactants": {"P": 4, "S": 3}},
    ("S", "Br"):   {"products": [("SBr2", 1)],     "energy": -50,   "equation": "S + Br\u2082 \u2192 SBr\u2082",
                    "min_reactants": {"S": 1, "Br": 2}},
    ("S", "I"):    {"products": [],               "energy": 0,     "equation": "(no stable iodine sulfide)", "min_reactants": {}},
    ("S", "B"):    {"products": [],               "energy": 0,     "equation": "(B\\u2082S\\u2083 needs catalyst)", "min_reactants": {}},
    ("S", "Be"):   {"products": [("BeS", 1)],      "energy": -234,  "equation": "Be + S \\u2192 BeS"},
    ("S", "Mg"):   {"products": [("MgS", 1)],      "energy": -347, "equation": "Mg + S \\u2192 MgS"},
    ("S", "Ca"):   {"products": [("CaS", 1)],      "energy": -482, "equation": "Ca + S \\u2192 CaS"},
    ("S", "Ba"):   {"products": [("BaS", 1)],      "energy": -460, "equation": "Ba + S \\u2192 BaS (as BaO+S proxy)"},
    ("S", "Ag"):   {"products": [("Ag2S", 1)],     "energy": -32,   "equation": "4Ag + 2H\\u2082S + O\\u2082 \\u2192 2Ag\\u2082S + 2H\\u2082O",
                    "min_reactants": {"Ag": 2, "S": 1}},
    ("S", "Zn"):   {"products": [("ZnS", 1)],      "energy": -206, "equation": "Zn + S \\u2192 ZnS"},
    ("S", "Cu"):   {"products": [("CuS", 1)],      "energy": -53,   "equation": "Cu + S \\u2192 CuS"},
    ("S", "Ni"):   {"products": [("NiS", 1)],      "energy": -82,   "equation": "Ni + S \\u2192 NiS"},
    ("S", "Mn"):   {"products": [("MnS", 1)],      "energy": -214,  "equation": "Mn + S \\u2192 MnS"},
    ("S", "Fe"):   {"products": [("FeS", 1)],      "energy": -100,  "equation": "Fe + S \\u2192 FeS"},
    ("S", "Cr"):   {"products": [("Cr2S3", 1)],    "energy": -460,  "equation": "2Cr + 3S \\u2192 Cr\\u2082S\\u2083",
                    "min_reactants": {"Cr": 2, "S": 3}},
    ("S", "Na"):   {"products": [("Na2S", 1)],     "energy": -364, "equation": "2Na + S \\u2192 Na\\u2082S",
                    "min_reactants": {"Na": 2, "S": 1}},
    ("S", "K"):    {"products": [("K2S", 1)],      "energy": -430, "equation": "2K + S \\u2192 K\\u2082S",
                    "min_reactants": {"K": 2, "S": 1}},
    ("S", "Li"):   {"products": [("Li2S", 1)],     "energy": -440, "equation": "2Li + S \\u2192 Li\\u2082S",
                    "min_reactants": {"Li": 2, "S": 1}},
    # --- Alloys (metal-metal at high temperature) ---
    ("Na", "K"):   {"products": [("NaK", 1)],      "energy": -1,    "equation": "Na + K \\u2192 NaK (alloy)"},
    ("Fe", "Ti"):  {"products": [("FeTi", 1)],     "energy": -35,   "equation": "Fe + Ti \\u2192 FeTi (ferrotitanium)"},
    ("Cu", "Zn"):   {"products": [("CuZn", 1)],     "energy": -12,   "equation": "Cu + Zn \\u2192 CuZn (brass)"},
    ("Cu", "Ni"):   {"products": [("CuNi", 1)],     "energy": -15,   "equation": "Cu + Ni \\u2192 CuNi (cupronickel)"},
    ("Fe", "Cr"):   {"products": [("FeCr", 1)],     "energy": -20,   "equation": "Fe + Cr \\u2192 FeCr (stainless steel base)"},
    ("Mn", "Fe"):   {"products": [("MnFe", 1)],     "energy": -14,   "equation": "Mn + Fe \\u2192 MnFe (ferromanganese)"},
    ("Ni", "Fe"):   {"products": [("NiFe", 1)],     "energy": -10,   "equation": "Ni + Fe \\u2192 NiFe (permalloy)"},
    ("Cr", "Ni"):   {"products": [("FeNiCr", 1)],  "energy": -15,   "equation": "Fe + Ni + Cr \\u2192 FeNiCr (stainless)"},
    ("Cr", "Ti"):   {"products": [],               "energy": 0,     "equation": "(TiCr\\u2082 needs catalyst)", "min_reactants": {}},
    ("Ti", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable Ti-Zn compound)", "min_reactants": {}},
    ("Ti", "Mn"):   {"products": [],               "energy": 0,     "equation": "(no stable Ti-Mn compound)", "min_reactants": {}},
    ("Ti", "Ni"):   {"products": [],               "energy": 0,     "equation": "(no stable Ti-Ni compound)", "min_reactants": {}},
    ("Ti", "Cu"):   {"products": [],               "energy": 0,     "equation": "(no stable Ti-Cu compound)", "min_reactants": {}},
    # --- Silicon remaining ---
    ("Si", "B"):    {"products": [],               "energy": 0,     "equation": "(B\\u2081\\u2082 needs catalyst)", "min_reactants": {}},
    ("Si", "N"):    {"products": [],               "energy": 0,     "equation": "(Si\\u2083N\\u2084 needs 4N)", "min_reactants": {}},
    ("Si", "Mg"):   {"products": [],               "energy": 0,     "equation": "(Mg\\u2082Si needs catalyst)", "min_reactants": {}},
    ("Si", "K"):    {"products": [],               "energy": 0,     "equation": "(no stable K-Si compound)", "min_reactants": {}},
    ("Si", "Li"):   {"products": [],               "energy": 0,     "equation": "(no stable Li-Si compound)", "min_reactants": {}},
    ("Si", "Na"):   {"products": [],               "energy": 0,     "equation": "(no stable Na-Si compound)", "min_reactants": {}},
    ("Si", "Ca"):   {"products": [],               "energy": 0,     "equation": "(no stable Ca-Si compound)", "min_reactants": {}},
    ("Si", "Ba"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Si compound)", "min_reactants": {}},
    ("Si", "P"):    {"products": [],               "energy": 0,     "equation": "(silicon phosphide needs catalyst)", "min_reactants": {}},
    # --- Phosphorus remaining ---
    ("P", "B"):    {"products": [],               "energy": 0,     "equation": "(BP needs catalyst)", "min_reactants": {}},
    ("P", "N"):    {"products": [],               "energy": 0,     "equation": "(PN needs catalyst)", "min_reactants": {}},
    ("P", "K"):    {"products": [],               "energy": 0,     "equation": "(no stable K-P compound)", "min_reactants": {}},
    ("P", "Na"):   {"products": [],               "energy": 0,     "equation": "(Na\\u2083P needs 3Na)", "min_reactants": {}},
    ("P", "Li"):   {"products": [],               "energy": 0,     "equation": "(Li\\u2083P needs 3Li)", "min_reactants": {}},
    ("P", "Mg"):   {"products": [],               "energy": 0,     "equation": "(Mg\\u2083P\\u2082 needs 3Mg)", "min_reactants": {}},
    ("P", "Ti"):   {"products": [],               "energy": 0,     "equation": "(TiP needs catalyst)", "min_reactants": {}},
    ("P", "Mn"):   {"products": [],               "energy": 0,     "equation": "(MnP needs catalyst)", "min_reactants": {}},
    ("P", "Fe"):   {"products": [],               "energy": 0,     "equation": "(Fe\\u2083P needs catalyst)", "min_reactants": {}},
    ("P", "Ni"):   {"products": [],               "energy": 0,     "equation": "(Ni\\u2082P needs catalyst)", "min_reactants": {}},
    ("P", "Cu"):   {"products": [],               "energy": 0,     "equation": "(Cu\\u2083P needs catalyst)", "min_reactants": {}},
    ("P", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable Zn-P compound)", "min_reactants": {}},
    ("P", "Ag"):   {"products": [],               "energy": 0,     "equation": "(no stable Ag-P compound)", "min_reactants": {}},
    ("P", "Au"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-P compound)", "min_reactants": {}},
    ("P", "Si"):   {"products": [],               "energy": 0,     "equation": "(silicon phosphide needs catalyst)", "min_reactants": {}},
    ("P", "Cr"):   {"products": [],               "energy": 0,     "equation": "(CrP needs catalyst)", "min_reactants": {}},
    ("P", "Ca"):   {"products": [],               "energy": 0,     "equation": "(Ca\\u2083(PO\\u2084)\\u2082 needs catalyst)", "min_reactants": {}},
    # --- Boron remaining ---
    ("B", "H"):    {"products": [],               "energy": 0,     "equation": "(B\\u2082H\\u2086 unstable)", "min_reactants": {}},
    ("B", "C"):    {"products": [],               "energy": 0,     "equation": "(B\\u2084C needs 4B + catalyst)", "min_reactants": {}},
    ("B", "K"):    {"products": [],               "energy": 0,     "equation": "(no stable K-B compound)", "min_reactants": {}},
    ("B", "Li"):   {"products": [],               "energy": 0,     "equation": "(no stable Li-B compound)", "min_reactants": {}},
    ("B", "Mg"):   {"products": [],               "energy": 0,     "equation": "(MgB\\u2081\\u2082 needs catalyst)", "min_reactants": {}},
    ("B", "Ti"):   {"products": [],               "energy": 0,     "equation": "(TiB\\u2082 needs catalyst)", "min_reactants": {}},
    ("B", "Mn"):   {"products": [],               "energy": 0,     "equation": "(MnB needs catalyst)", "min_reactants": {}},
    ("B", "Fe"):   {"products": [],               "energy": 0,     "equation": "(FeB needs catalyst)", "min_reactants": {}},
    ("B", "Ni"):   {"products": [],               "energy": 0,     "equation": "(NiB needs catalyst)", "min_reactants": {}},
    ("B", "Cu"):   {"products": [],               "energy": 0,     "equation": "(CuB needs catalyst)", "min_reactants": {}},
    ("B", "Zn"):   {"products": [],               "energy": 0,     "equation": "(ZnB needs catalyst)", "min_reactants": {}},
    ("B", "Ag"):   {"products": [],               "energy": 0,     "equation": "(no stable Ag-B compound)", "min_reactants": {}},
    ("B", "Au"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-B compound)", "min_reactants": {}},
    ("B", "Cr"):   {"products": [],               "energy": 0,     "equation": "(CrB\\u2082 needs catalyst)", "min_reactants": {}},
    ("B", "Ca"):   {"products": [],               "energy": 0,     "equation": "(CaB\\u2086 needs catalyst)", "min_reactants": {}},
    ("B", "Ba"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-B compound)", "min_reactants": {}},
    # --- Iodine remaining ---
    ("I", "N"):    {"products": [],               "energy": 0,     "equation": "(NI\\u2083 needs 3I)", "min_reactants": {}},
    ("I", "S"):    {"products": [],               "energy": 0,     "equation": "(no stable iodine sulfide)", "min_reactants": {}},
    ("I", "Mg"):   {"products": [("MgI2", 1)],     "energy": -366,  "equation": "Mg + I\u2082 \u2192 MgI\u2082",
                    "min_reactants": {"Mg": 1, "I": 2}},
    ("I", "Ca"):   {"products": [("CaI2", 1)],     "energy": -535,  "equation": "Ca + I\u2082 \u2192 CaI\u2082",
                    "min_reactants": {"Ca": 1, "I": 2}},
    ("I", "Ba"):   {"products": [("BaI2", 1)],     "energy": -602,  "equation": "Ba + I\u2082 \u2192 BaI\u2082",
                    "min_reactants": {"Ba": 1, "I": 2}},
    ("I", "Ag"):   {"products": [("AgI", 1)],      "energy": -118,  "equation": "Ag + I \u2192 AgI"},
    ("I", "Au"):   {"products": [],               "energy": 0,     "equation": "(AuI\\u2083 needs 3I)", "min_reactants": {}},
    ("I", "Br"):   {"products": [],               "energy": 0,     "equation": "(IBr already exists)", "min_reactants": {}},
    # --- Bromine remaining ---
    ("Br", "N"):   {"products": [("NBr3", 1)],     "energy": 270,   "equation": "N\u2082 + 3Br\u2082 \u2192 2NBr\u2083 (endothermic)",
                    "min_reactants": {"N": 1, "Br": 3}},
    ("Br", "Mg"):   {"products": [],               "energy": 0,     "equation": "(MgBr\\u2082 already exists via Mg,Br)", "min_reactants": {}},
    ("Br", "Ca"):   {"products": [],               "energy": 0,     "equation": "(CaBr\\u2082 already exists via Ca,Br)", "min_reactants": {}},
    ("Br", "Ba"):   {"products": [],               "energy": 0,     "equation": "(BaBr\\u2082 needs 2Br)", "min_reactants": {}},
    ("Br", "Ti"):   {"products": [("TiBr4", 1)],    "energy": -550,  "equation": "Ti + 2Br\u2082 \u2192 TiBr\u2084",
                    "min_reactants": {"Ti": 1, "Br": 4}},
    ("Br", "Mn"):   {"products": [("MnBr2", 1)],    "energy": -340,  "equation": "Mn + Br\u2082 \u2192 MnBr\u2082",
                    "min_reactants": {"Mn": 1, "Br": 2}},
    ("Br", "Fe"):   {"products": [("FeBr2", 1)],    "energy": -250,  "equation": "Fe + Br\u2082 \u2192 FeBr\u2082",
                    "min_reactants": {"Fe": 1, "Br": 2}},
    ("Br", "Ni"):   {"products": [("NiBr2", 1)],    "energy": -210,  "equation": "Ni + Br\u2082 \u2192 NiBr\u2082",
                    "min_reactants": {"Ni": 1, "Br": 2}},
    ("Br", "Cu"):   {"products": [("CuBr2", 1)],    "energy": -172,  "equation": "Cu + Br\u2082 \u2192 CuBr\u2082",
                    "min_reactants": {"Cu": 1, "Br": 2}},
    ("Br", "Zn"):   {"products": [("ZnBr2", 1)],    "energy": -320,  "equation": "Zn + Br\u2082 \u2192 ZnBr\u2082",
                    "min_reactants": {"Zn": 1, "Br": 2}},
    # --- Noble gases (all inert) ---
    ("He", "H"):   {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "O"):   {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "C"):   {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "N"):   {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "F"):   {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "Cl"):  {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "S"):   {"products": [],               "energy": 0,     "equation": "(He is inert noble gas)", "min_reactants": {}},
    ("He", "Ne"):   {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("He", "Ar"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ne", "H"):   {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("Ne", "O"):   {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("Ne", "N"):   {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("Ne", "F"):   {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("Ne", "Cl"):  {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("Ne", "S"):   {"products": [],               "energy": 0,     "equation": "(Ne is inert noble gas)", "min_reactants": {}},
    ("Ne", "Ar"):   {"products": [],               "energy": 0,     "equation": "(Ne, Ar inert noble gases)", "min_reactants": {}},
    ("Ar", "H"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "O"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "N"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "F"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "Cl"):  {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "S"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "Si"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    ("Ar", "C"):   {"products": [],               "energy": 0,     "equation": "(Ar is inert noble gas)", "min_reactants": {}},
    # --- Silver & Gold remaining ---
    ("Ag", "H"):   {"products": [],               "energy": 0,     "equation": "(AgH unstable above 100K)", "min_reactants": {}},
    ("Ag", "N"):   {"products": [],               "energy": 0,     "equation": "(Ag\\u2083N needs 3N)", "min_reactants": {}},
    ("Ag", "C"):   {"products": [],               "energy": 0,     "equation": "(AgC needs catalyst)", "min_reactants": {}},
    ("Ag", "Si"):  {"products": [],               "energy": 0,     "equation": "(no stable Ag-Si compound)", "min_reactants": {}},
    ("Ag", "P"):   {"products": [],               "energy": 0,     "equation": "(no stable Ag-P compound)", "min_reactants": {}},
    ("Ag", "Ti"):   {"products": [],               "energy": 0,     "equation": "(no stable Ag-Ti compound)", "min_reactants": {}},
    ("Ag", "Mn"):   {"products": [],               "energy": 0,     "equation": "(AgMn needs catalyst)", "min_reactants": {}},
    ("Ag", "Cu"):   {"products": [],               "energy": 0,     "equation": "(no stable Ag-Cu compound)", "min_reactants": {}},
    ("Ag", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable Ag-Zn compound)", "min_reactants": {}},
    ("Au", "H"):   {"products": [],               "energy": 0,     "equation": "(Au is unreactive with H)", "min_reactants": {}},
    ("Au", "N"):   {"products": [],               "energy": 0,     "equation": "(Au is unreactive with N)", "min_reactants": {}},
    ("Au", "C"):   {"products": [],               "energy": 0,     "equation": "(Au is unreactive with C)", "min_reactants": {}},
    ("Au", "O"):   {"products": [],               "energy": 0,     "equation": "(Au resists oxidation)", "min_reactants": {}},
    ("Au", "S"):   {"products": [],               "energy": 0,     "equation": "(Au\\u2082S\\u2083 at extreme T only)", "min_reactants": {}},
    ("Au", "Si"):  {"products": [],               "energy": 0,     "equation": "(no stable Au-Si compound)", "min_reactants": {}},
    ("Au", "P"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-P compound)", "min_reactants": {}},
    ("Au", "Ti"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Ti compound)", "min_reactants": {}},
    ("Au", "Mn"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Mn compound)", "min_reactants": {}},
    ("Au", "Cu"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Cu compound)", "min_reactants": {}},
    ("Au", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Zn compound)", "min_reactants": {}},
    ("Au", "Cr"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Cr compound)", "min_reactants": {}},
    ("Au", "Ca"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Ca compound)", "min_reactants": {}},
    ("Au", "Ba"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-Ba compound)", "min_reactants": {}},
    ("Au", "B"):   {"products": [],               "energy": 0,     "equation": "(no stable Au-B compound)", "min_reactants": {}},
    # --- Be remaining ---
    ("Be", "H"):   {"products": [],               "energy": 0,     "equation": "(BeH\\u2082 unstable)", "min_reactants": {}},
    ("Be", "C"):   {"products": [],               "energy": 0,     "equation": "(Be\\u2082C needs catalyst)", "min_reactants": {}},
    ("Be", "N"):   {"products": [],               "energy": 0,     "equation": "(Be\\u2083N\\u2082 needs 2Be)", "min_reactants": {}},
    ("Be", "K"):    {"products": [],               "energy": 0,     "equation": "(no stable Be-K compound)", "min_reactants": {}},
    ("Be", "Li"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Li compound)", "min_reactants": {}},
    ("Be", "Mg"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Mg compound)", "min_reactants": {}},
    ("Be", "Ti"):   {"products": [],               "energy": 0,     "equation": "(BeTi needs catalyst)", "min_reactants": {}},
    ("Be", "Mn"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Mn compound)", "min_reactants": {}},
    ("Be", "Fe"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Fe compound)", "min_reactants": {}},
    ("Be", "Ni"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Ni compound)", "min_reactants": {}},
    ("Be", "Cu"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Cu compound)", "min_reactants": {}},
    ("Be", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Zn compound)", "min_reactants": {}},
    ("Be", "Ag"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Ag compound)", "min_reactants": {}},
    ("Be", "Au"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Au compound)", "min_reactants": {}},
    ("Be", "Cr"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Cr compound)", "min_reactants": {}},
    ("Be", "Ca"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Ca compound)", "min_reactants": {}},
    ("Be", "Ba"):   {"products": [],               "energy": 0,     "equation": "(no stable Be-Ba compound)", "min_reactants": {}},
    # --- Ba remaining ---
    ("Ba", "H"):   {"products": [("BaH2", 1)],     "energy": -178,  "equation": "Ba + H\u2082 \u2192 BaH\u2082",
                    "min_reactants": {"Ba": 1, "H": 2}},
    ("Ba", "N"):   {"products": [],               "energy": 0,     "equation": "(BaN\\u2083 needs 3Ba)", "min_reactants": {}},
    ("Ba", "C"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-C compound)", "min_reactants": {}},
    ("Ba", "K"):    {"products": [],               "energy": 0,     "equation": "(no stable Ba-K compound)", "min_reactants": {}},
    ("Ba", "Li"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Li compound)", "min_reactants": {}},
    ("Ba", "Mg"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Mg compound)", "min_reactants": {}},
    ("Ba", "Ti"):   {"products": [],               "energy": 0,     "equation": "(BaTiO\\u2083 needs 3O)", "min_reactants": {}},
    ("Ba", "Mn"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Mn compound)", "min_reactants": {}},
    ("Ba", "Fe"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Fe compound)", "min_reactants": {}},
    ("Ba", "Ni"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Ni compound)", "min_reactants": {}},
    ("Ba", "Cu"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Cu compound)", "min_reactants": {}},
    ("Ba", "Zn"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Zn compound)", "min_reactants": {}},
    ("Ba", "Cr"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-Cr compound)", "min_reactants": {}},
    ("Ba", "Si"):   {"products": [],               "energy": 0,     "equation": "(BaSiO\\u2083 needs 3O)", "min_reactants": {}},
    ("Ba", "P"):   {"products": [],               "energy": 0,     "equation": "(no stable Ba-P compound)", "min_reactants": {}},
    # === NEW REACTIONS BATCH 4: 30+ newly activated pathways ===
    # --- Metal + Iodine (new entries) ---
    ("Ag", "Br"):  {"products": [("AgBr", 1)],     "energy": -100,  "equation": "Ag + Br \u2192 AgBr"},
    ("Cu", "I"):   {"products": [("CuI", 1)],       "energy": -85,   "equation": "Cu + I \u2192 CuI"},
    ("Fe", "I"):   {"products": [("FeI2", 1)],     "energy": -150,  "equation": "Fe + I\u2082 \u2192 FeI\u2082",
                    "min_reactants": {"Fe": 1, "I": 2}},
    ("Ni", "I"):   {"products": [("NiI2", 1)],     "energy": -130,  "equation": "Ni + I\u2082 \u2192 NiI\u2082",
                    "min_reactants": {"Ni": 1, "I": 2}},
    ("Zn", "I"):   {"products": [("ZnI2", 1)],     "energy": -210,  "equation": "Zn + I\u2082 \u2192 ZnI\u2082",
                    "min_reactants": {"Zn": 1, "I": 2}},
    ("Be", "I"):   {"products": [("BeI2", 1)],     "energy": -190,  "equation": "Be + I\u2082 \u2192 BeI\u2082",
                    "min_reactants": {"Be": 1, "I": 2}},
    ("Be", "Br"):  {"products": [("BeBr2", 1)],    "energy": -310,  "equation": "Be + Br\u2082 \u2192 BeBr\u2082",
                    "min_reactants": {"Be": 1, "Br": 2}},
    ("Cr", "Br"):  {"products": [("CrBr3", 1)],    "energy": -420,  "equation": "2Cr + 3Br\u2082 \u2192 2CrBr\u2083",
                    "min_reactants": {"Cr": 1, "Br": 3}},
    # --- Metal + Iodine (more) ---
    ("Ti", "I"):   {"products": [],               "energy": 0,     "equation": "(TiI\u2084 needs 4I)", "min_reactants": {}},
    ("Mn", "I"):   {"products": [],               "energy": 0,     "equation": "(MnI\u2082 needs 2I)", "min_reactants": {}},
    ("Cu", "Br"):  {"products": [("CuBr2", 1)],    "energy": -172,  "equation": "Cu + Br\u2082 \u2192 CuBr\u2082",
                    "min_reactants": {"Cu": 1, "Br": 2}},
    ("Fe", "Br"):  {"products": [("FeBr2", 1)],    "energy": -250,  "equation": "Fe + Br\u2082 \u2192 FeBr\u2082",
                    "min_reactants": {"Fe": 1, "Br": 2}},
    ("Ni", "Br"):  {"products": [("NiBr2", 1)],    "energy": -210,  "equation": "Ni + Br\u2082 \u2192 NiBr\u2082",
                    "min_reactants": {"Ni": 1, "Br": 2}},
    ("Zn", "Br"):  {"products": [("ZnBr2", 1)],    "energy": -320,  "equation": "Zn + Br\u2082 \u2192 ZnBr\u2082",
                    "min_reactants": {"Zn": 1, "Br": 2}},
    ("Mn", "Br"):  {"products": [("MnBr2", 1)],    "energy": -340,  "equation": "Mn + Br\u2082 \u2192 MnBr\u2082",
                    "min_reactants": {"Mn": 1, "Br": 2}},
    ("Ti", "Br"):  {"products": [("TiBr4", 1)],    "energy": -550,  "equation": "Ti + 2Br\u2082 \u2192 TiBr\u2084",
                    "min_reactants": {"Ti": 1, "Br": 4}},
    # --- Additional oxide pathways (alt products) ---
    ("Na", "O"):   {"products": [("Na2O2", 1)],    "energy": -518,  "equation": "2Na + O\u2082 \u2192 Na\u2082O\u2082 (peroxide)",
                    "min_reactants": {"Na": 2, "O": 2}, "alt": True},
    ("K", "O"):    {"products": [("KO2", 1)],       "energy": -284,  "equation": "K + O\u2082 \u2192 KO\u2082 (superoxide)",
                    "min_reactants": {"K": 1, "O": 2}, "alt": True},
    ("Li", "O"):   {"products": [("Li2O2", 1)],    "energy": -598,  "equation": "2Li + O\u2082 \u2192 Li\u2082O\u2082 (peroxide)",
                    "min_reactants": {"Li": 2, "O": 2}, "alt": True},
    ("Cu", "O"):   {"products": [("Cu2O", 1)],      "energy": -169,  "equation": "4Cu + O\u2082 \u2192 2Cu\u2082O (cuprous oxide)",
                    "min_reactants": {"Cu": 2, "O": 1}, "alt": True},
    # --- Acid formation (simplified) ---
    ("S", "H"):    {"products": [("H2SO4", 1)],    "energy": -814,  "equation": "H\u2082 + S + 2O\u2082 \u2192 H\u2082SO\u2084",
                    "min_reactants": {"S": 1, "H": 2, "O": 4}, "alt": True},
    ("N", "H"):    {"products": [("HNO3", 1)],     "energy": -207,  "equation": "N\u2082 + H\u2082 + 3O\u2082 \u2192 2HNO\u2083",
                    "min_reactants": {"N": 1, "H": 1, "O": 3}, "alt": True},
    ("P", "H"):    {"products": [("H3PO4", 1)],    "energy": -1281, "equation": "P + 2H\u2082 + 2O\u2082 \u2192 H\u2083PO\u2084",
                    "min_reactants": {"P": 1, "H": 3, "O": 4}, "alt": True},
}

NORMALIZED_REACTIONS = {}
for (a, b), v in REACTIONS.items():
    key = tuple(sorted([a, b]))
    if key not in NORMALIZED_REACTIONS or not v.get("alt", False):
        NORMALIZED_REACTIONS[key] = v


# ─── Sound Generator ─────────────────────────────────────────────────────────
class SoundGenerator:
    """Generate procedural sound effects using pygame.mixer."""
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.available = True
        except Exception:
            self.available = False

    def _make_sound(self, freq, duration, volume=0.3, wave="sine", freq_end=None):
        if not self.available:
            return None
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        if freq_end is None:
            freq_end = freq
        for i in range(n_samples):
            t = i / sample_rate
            progress = i / n_samples
            f = freq + (freq_end - freq) * progress
            if wave == "sine":
                val = math.sin(2 * math.pi * f * t)
            elif wave == "square":
                val = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0
            elif wave == "noise":
                val = random.uniform(-1, 1) * math.sin(2 * math.pi * f * t)
            else:
                val = math.sin(2 * math.pi * f * t)
            # Envelope: quick attack, exponential decay
            envelope = min(1.0, i / (sample_rate * 0.01)) * math.exp(-progress * 4)
            buf[i] = int(val * volume * 32767 * envelope)
        sound = pygame.mixer.Sound(buffer=buf)
        return sound

    def play_reaction(self, energy):
        if not self.enabled or not self.available:
            return
        try:
            if energy < -400:
                # Vigorous exothermic - deep boom
                s = self._make_sound(80, 0.5, 0.4, "noise", 30)
                if s: s.play()
            elif energy < -100:
                # Moderate exothermic - pop
                s = self._make_sound(300, 0.2, 0.25, "sine", 100)
                if s: s.play()
            elif energy < 0:
                # Mild exothermic
                s = self._make_sound(500, 0.15, 0.15, "sine", 300)
                if s: s.play()
            else:
                # Endothermic -吸入
                s = self._make_sound(200, 0.3, 0.2, "sine", 600)
                if s: s.play()
        except Exception:
            pass

    def play_decomp(self):
        if not self.enabled or not self.available:
            return
        try:
            s = self._make_sound(600, 0.25, 0.2, "square", 200)
            if s: s.play()
        except Exception:
            pass

    def play_spawn(self):
        if not self.enabled or not self.available:
            return
        try:
            s = self._make_sound(800, 0.08, 0.1, "sine", 1200)
            if s: s.play()
        except Exception:
            pass

    def toggle(self):
        self.enabled = not self.enabled


# ─── Particle Class ──────────────────────────────────────────────────────────
class Particle:
    _font_cache = {}

    def __init__(self, x, y, symbol, vx=None, vy=None, is_molecule=False, mol_key=None):
        self.x = float(x)
        self.y = float(y)
        self.symbol = symbol
        self.is_molecule = is_molecule
        self.mol_key = mol_key

        if is_molecule and mol_key and mol_key in MOLECULE_TYPES:
            info = MOLECULE_TYPES[mol_key]
            self.color = info["color"]
            self.radius = info["radius"]
            self.mass = info["mass"]
            self.formula = info["formula"]
        elif symbol in ATOM_TYPES:
            info = ATOM_TYPES[symbol]
            self.color = info["color"]
            self.radius = info["radius"]
            self.mass = info["mass"]
            self.formula = symbol
        else:
            self.color = (200, 200, 200)
            self.radius = 15
            self.mass = 10
            self.formula = symbol

        speed = 2.0
        self.vx = vx if vx is not None else random.uniform(-speed, speed)
        self.vy = vy if vy is not None else random.uniform(-speed, speed)

        self.alive = True
        self.age = 0.0
        self.glow_timer = 0.0
        self.trail = deque(maxlen=15)
        self.pulse_phase = random.uniform(0, 2 * math.pi)
        self.rotation = random.uniform(0, 2 * math.pi)
        self.rot_speed = random.uniform(-1.5, 1.5)
        # For molecule structure rendering
        self.atom_offsets = []
        if is_molecule and mol_key and mol_key in MOLECULE_TYPES:
            self._compute_atom_layout()

    def _compute_atom_layout(self):
        """Compute relative positions of atoms within a molecule."""
        mol = MOLECULE_TYPES[self.mol_key]
        atoms = mol["atoms"]
        n = len(atoms)
        self.atom_offsets = []
        if n == 2:
            self.atom_offsets = [(-8, 0), (8, 0)]
        elif n == 3:
            self.atom_offsets = [(0, -9), (-8, 7), (8, 7)]
        elif n == 4:
            self.atom_offsets = [(0, -9), (-9, 5), (9, 5), (0, 0)]
            # tetrahedral-ish: 3 around + 1 top
            self.atom_offsets = [(-7, -6), (7, -6), (-7, 8), (7, 8)]
        elif n == 5:
            self.atom_offsets = [(-9, -6), (9, -6), (-9, 8), (9, 8), (0, -10)]

    @staticmethod
    def _get_font(size, bold=False):
        key = (size, bold)
        if key not in Particle._font_cache:
            Particle._font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold)
        return Particle._font_cache[key]

    def kinetic_energy(self):
        return 0.5 * self.mass * (self.vx**2 + self.vy**2)

    def speed(self):
        return math.hypot(self.vx, self.vy)

    def update(self, dt, speed_mult, gravity, sim_rect, temperature):
        self.age += dt
        self.pulse_phase += dt * 3
        if self.glow_timer > 0:
            self.glow_timer -= dt * 1.5
        self.rotation += self.rot_speed * dt * speed_mult

        self.trail.append((self.x, self.y))

        # Temperature affects velocity - Brownian motion
        if not self.is_molecule:
            temp_factor = temperature / 300.0
            brownian = 0.02 * math.sqrt(temp_factor) * speed_mult
            self.vx += random.gauss(0, brownian)
            self.vy += random.gauss(0, brownian)

        # Gravity
        if gravity:
            self.vy += 0.15 * speed_mult

        # Thermostat: gently nudge speeds toward temperature-appropriate range
        target_speed = 1.5 * math.sqrt(temperature / 300.0)
        current_speed = self.speed()
        if current_speed > 0.01:
            ratio = 1.0 + (target_speed / current_speed - 1.0) * 0.01
            self.vx *= ratio
            self.vy *= ratio

        # Move
        self.x += self.vx * speed_mult * dt * 60
        self.y += self.vy * speed_mult * dt * 60

        # Bounce off walls
        left, top, right, bottom = sim_rect
        if self.x - self.radius < left:
            self.x = left + self.radius
            self.vx = abs(self.vx) * 0.95
        if self.x + self.radius > right:
            self.x = right - self.radius
            self.vx = -abs(self.vx) * 0.95
        if self.y - self.radius < top:
            self.y = top + self.radius
            self.vy = abs(self.vy) * 0.95
        if self.y + self.radius > bottom:
            self.y = bottom - self.radius
            self.vy = -abs(self.vy) * 0.95

    def draw(self, surface, show_structure):
        # Trail
        trail_list = list(self.trail)
        for i, (tx, ty) in enumerate(trail_list):
            alpha = (i + 1) / len(trail_list) * 0.25
            trail_r = max(2, int(self.radius * alpha * 0.8))
            trail_color = tuple(max(0, min(255, int(c * alpha))) for c in self.color)
            pygame.draw.circle(surface, trail_color, (int(tx), int(ty)), trail_r)

        cx, cy = int(self.x), int(self.y)

        # Outer glow ring
        pulse = math.sin(self.pulse_phase) * 0.12 + 0.88
        glow_r = int(self.radius * 1.6 * pulse)
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 20), (glow_r + 2, glow_r + 2), glow_r)
        surface.blit(glow_surf, (cx - glow_r - 2, cy - glow_r - 2))

        # Reaction glow
        if self.glow_timer > 0:
            gi = min(1.0, self.glow_timer)
            gr = int(self.radius * 3.5 * gi)
            gs = pygame.Surface((gr * 2 + 4, gr * 2 + 4), pygame.SRCALPHA)
            for r in range(gr, 0, -3):
                a = int(50 * gi * (r / gr))
                pygame.draw.circle(gs, (*self.color, a), (gr + 2, gr + 2), r)
            surface.blit(gs, (cx - gr - 2, cy - gr - 2))

        if show_structure and self.is_molecule and self.atom_offsets:
            self._draw_molecule_structure(surface, cx, cy)
        else:
            self._draw_simple(surface, cx, cy)

    def _draw_simple(self, surface, cx, cy):
        """Draw a simple gradient circle with label."""
        for r in range(self.radius, 0, -1):
            frac = r / self.radius
            bright = 0.45 + 0.55 * (1 - frac)
            c = tuple(min(255, int(comp * bright)) for comp in self.color)
            pygame.draw.circle(surface, c, (cx, cy), r)
        # Specular highlight
        hx = int(self.x - self.radius * 0.25)
        hy = int(self.y - self.radius * 0.25)
        hr = max(2, int(self.radius * 0.28))
        hs = pygame.Surface((hr * 2 + 2, hr * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(hs, (255, 255, 255, 90), (hr + 1, hr + 1), hr)
        surface.blit(hs, (hx - hr - 1, hy - hr - 1))
        # Label
        fs = max(10, int(self.radius * 0.75))
        font = self._get_font(fs, bold=True)
        label = font.render(self.formula, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=(cx, cy)))

    def _draw_molecule_structure(self, surface, cx, cy):
        """Draw atoms with bonds for molecules."""
        mol = MOLECULE_TYPES.get(self.mol_key, {})
        atoms_list = mol.get("atoms", [])
        bonds = mol.get("bond_order", [])

        cos_r = math.cos(self.rotation)
        sin_r = math.sin(self.rotation)
        scale = self.radius / 18.0

        # Compute world positions of sub-atoms
        positions = []
        for ox, oy in self.atom_offsets:
            rx = ox * cos_r - oy * sin_r
            ry = ox * sin_r + oy * cos_r
            px = cx + rx * scale
            py = cy + ry * scale
            positions.append((px, py))

        # Draw bonds
        bond_pairs = []
        if len(atoms_list) >= 2:
            # Connect first atom to all others (simplified)
            for i in range(1, len(atoms_list)):
                bond_pairs.append((0, i))

        for idx, (i, j) in enumerate(bond_pairs):
            if idx < len(bonds):
                order = bonds[idx]
            else:
                order = 1
            x1, y1 = positions[i]
            x2, y2 = positions[j]
            self._draw_bond(surface, x1, y1, x2, y2, order)

        # Draw sub-atoms
        for i, (px, py) in enumerate(positions):
            if i < len(atoms_list):
                sym = atoms_list[i]
                ainfo = ATOM_TYPES.get(sym, {})
                ac = ainfo.get("color", (180, 180, 180))
                ar = max(4, int((ainfo.get("radius", 10) * 0.6) * scale))
                # Mini gradient
                for r in range(ar, 0, -1):
                    f = r / ar
                    bright = 0.5 + 0.5 * (1 - f)
                    c = tuple(min(255, int(comp * bright)) for comp in ac)
                    pygame.draw.circle(surface, c, (int(px), int(py)), r)
                # Tiny label
                if ar >= 6:
                    fs = max(7, ar - 2)
                    font = self._get_font(fs, bold=True)
                    lbl = font.render(sym, True, (255, 255, 255))
                    surface.blit(lbl, lbl.get_rect(center=(int(px), int(py))))

    def _draw_bond(self, surface, x1, y1, x2, y2, order):
        """Draw a bond line (single, double, or triple)."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < 1:
            return
        nx = -dy / length * 2.5
        ny = dx / length * 2.5
        color = (180, 180, 200)
        if order == 1:
            pygame.draw.line(surface, color, (int(x1), int(y1)), (int(x2), int(y2)), 2)
        elif order == 2:
            pygame.draw.line(surface, color, (int(x1 + nx), int(y1 + ny)), (int(x2 + nx), int(y2 + ny)), 2)
            pygame.draw.line(surface, color, (int(x1 - nx), int(y1 - ny)), (int(x2 - nx), int(y2 - ny)), 2)
        elif order >= 3:
            pygame.draw.line(surface, color, (int(x1), int(y1)), (int(x2), int(y2)), 2)
            pygame.draw.line(surface, color, (int(x1 + nx), int(y1 + ny)), (int(x2 + nx), int(y2 + ny)), 1)
            pygame.draw.line(surface, color, (int(x1 - nx), int(y1 - ny)), (int(x2 - nx), int(y2 - ny)), 1)


# ─── Shockwave Effect ────────────────────────────────────────────────────────
class Shockwave:
    def __init__(self, x, y, max_radius, color, speed=200):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = max_radius
        self.color = color
        self.speed = speed
        self.alive = True

    def update(self, dt):
        self.radius += self.speed * dt
        if self.radius >= self.max_radius:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        progress = self.radius / self.max_radius
        alpha = int(120 * (1 - progress))
        r = int(self.radius)
        if r < 2 or alpha < 5:
            return
        size = r * 2 + 4
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = (*self.color, alpha)
        pygame.draw.circle(s, c, (r + 2, r + 2), r, max(1, int(3 * (1 - progress))))
        surface.blit(s, (int(self.x) - r - 2, int(self.y) - r - 2))


# ─── Spark Effect ────────────────────────────────────────────────────────────
class Spark:
    def __init__(self, x, y, color, intensity=1.0):
        self.color = color
        self.particles = []
        count = int(18 * intensity)
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1, 6) * intensity
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd,
                "life": random.uniform(0.2, 0.7),
                "max_life": 0.7,
                "radius": random.uniform(1, 3.5) * intensity,
            })
        self.alive = True

    def update(self, dt):
        any_alive = False
        for p in self.particles:
            if p["life"] > 0:
                p["life"] -= dt
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vx"] *= 0.95
                p["vy"] *= 0.95
                any_alive = True
        self.alive = any_alive

    def draw(self, surface):
        for p in self.particles:
            if p["life"] > 0:
                alpha = max(0, p["life"] / p["max_life"])
                r = max(1, int(p["radius"] * alpha))
                c = tuple(min(255, int(comp * alpha + 255 * (1 - alpha) * 0.3)) for comp in self.color)
                pygame.draw.circle(surface, c, (int(p["x"]), int(p["y"])), r)


# ─── Energy Graph ─────────────────────────────────────────────────────────────
class EnergyGraph:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.data = deque(maxlen=200)
        self.total_energy = 0.0
        self.max_val = 100

    def add_energy(self, amount):
        self.total_energy += abs(amount)
        self.data.append(self.total_energy)
        if self.total_energy > self.max_val:
            self.max_val = self.total_energy * 1.2

    def draw(self, surface, font_small):
        # Background
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surface, (15, 15, 30), rect, border_radius=4)
        pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=4)

        if len(self.data) < 2:
            label = font_small.render("Awaiting reactions...", True, (80, 80, 120))
            surface.blit(label, (self.x + 10, self.y + self.h // 2 - 7))
            return

        # Draw axes
        margin = 5
        gx = self.x + margin
        gy = self.y + margin
        gw = self.w - margin * 2
        gh = self.h - margin * 2

        # Plot
        points = []
        data_list = list(self.data)
        for i, val in enumerate(data_list):
            px = gx + (i / max(1, len(data_list) - 1)) * gw
            py = gy + gh - (val / max(1, self.max_val)) * gh
            points.append((px, py))

        if len(points) >= 2:
            # Fill area under curve
            fill_points = [(points[0][0], gy + gh)] + points + [(points[-1][0], gy + gh)]
            fill_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            adjusted = [(p[0] - self.x, p[1] - self.y) for p in fill_points]
            if len(adjusted) >= 3:
                try:
                    pygame.gfxdraw.filled_polygon(fill_surf, adjusted, (80, 160, 255, 30))
                except Exception:
                    pass
            surface.blit(fill_surf, (self.x, self.y))

            # Line
            pygame.draw.lines(surface, (100, 180, 255), False, [(int(p[0]), int(p[1])) for p in points], 2)

        # Current value
        label = font_small.render(f"{self.total_energy:.0f} kJ", True, (100, 180, 255))
        surface.blit(label, (self.x + 8, self.y + 4))


# ─── Screen Shake ────────────────────────────────────────────────────────────
class ScreenShake:
    def __init__(self):
        self.intensity = 0.0
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, intensity):
        self.intensity = max(self.intensity, intensity)

    def update(self, dt):
        if self.intensity > 0.1:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity *= 0.88
        else:
            self.intensity = 0
            self.offset_x = 0
            self.offset_y = 0


# ─── Tool Modes ──────────────────────────────────────────────────────────────
TOOL_MODES = [
    {"id": "spawn",   "name": "Spawn",   "icon": "\u2795", "desc": "Click/drag to launch atoms"},
    {"id": "attract", "name": "Attract", "icon": "\u2b05", "desc": "Hold click to attract particles"},
    {"id": "repel",   "name": "Repel",   "icon": "\u27a1", "desc": "Hold click to repel particles"},
    {"id": "heat",    "name": "Heat",    "icon": "\U0001f525", "desc": "Click to raise local temperature"},
    {"id": "cool",    "name": "Cool",    "icon": "\u2744", "desc": "Click to lower local temperature"},
    {"id": "delete",  "name": "Delete",  "icon": "\u2716", "desc": "Click on particles to remove them"},
]


# ─── Main Simulation ─────────────────────────────────────────────────────────
class ChemicalSimulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chemical Reaction Simulator v4")
        self.clock = pygame.time.Clock()

        self.sim_rect = (10, 10, SIM_WIDTH - 20, HEIGHT - 20)
        self.particles = []
        self.sparks = []
        self.shockwaves = []
        self.paused = False
        self.speed_mult = 1.0
        self.gravity = False
        self.show_structure = True

        # Temperature
        self.temperature = 300.0
        self.temp_preset_idx = 2  # Room Temp
        self.local_heat_zones = []  # (x, y, radius, delta_temp, timer)

        # Tools
        self.tool_modes = TOOL_MODES
        self.tool_index = 0
        self.current_tool = self.tool_modes[0]

        # Atom selection
        self.atom_keys = list(ATOM_TYPES.keys())
        self.selected_index = 0
        self.selected_atom = self.atom_keys[0]

        # Drag-to-launch
        self.dragging = False
        self.drag_start = None
        self.drag_current = None

        # Continuous emitter
        self.emitting = False
        self.emit_timer = 0

        # Mouse force
        self.mouse_held = False
        self.mouse_pos = (0, 0)

        # Stats
        self.reaction_count = 0
        self.energy_released = 0.0
        self.decomp_count = 0

        # Effects
        self.shake = ScreenShake()
        self.sound = SoundGenerator()
        self.energy_graph = EnergyGraph(PANEL_X + 10, 0, PANEL_WIDTH - 20, 90)

        # Reaction log
        self.reaction_log = []

        # Undo
        self.spawn_history = deque(maxlen=50)

        # Hover
        self.hovered_particle = None

        # Fonts
        self.font_large = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 15)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.font_tiny = pygame.font.SysFont("Arial", 10)
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_symbol = pygame.font.SysFont("Arial", 28, bold=True)

        # Tooltip surface
        self.tooltip_surface = None

        # Screenshot counter
        self.screenshot_count = 0

        self._spawn_initial()

    def _spawn_initial(self):
        configs = [
            ("H", 14), ("O", 10), ("C", 7), ("N", 6),
            ("Na", 4), ("Cl", 5), ("F", 3), ("S", 3), ("Fe", 3), ("Ca", 2),
            ("Li", 2), ("Mg", 2), ("K", 2), ("Si", 2), ("Br", 2),
            ("Ti", 1), ("Cu", 1), ("Zn", 1), ("Ag", 1), ("P", 2),
        ]
        for symbol, count in configs:
            for _ in range(count):
                x = random.uniform(self.sim_rect[0] + 30, self.sim_rect[2] - 30)
                y = random.uniform(self.sim_rect[1] + 30, self.sim_rect[3] - 30)
                self.particles.append(Particle(x, y, symbol))

    def _get_effective_temperature(self, x, y):
        """Get local temperature at a point (affected by heat/cool zones)."""
        temp = self.temperature
        for hx, hy, hr, delta, timer in self.local_heat_zones:
            dist = math.hypot(x - hx, y - hy)
            if dist < hr:
                factor = 1.0 - (dist / hr)
                temp += delta * factor * timer
        return max(10, temp)

    def _try_reaction(self, p1, p2, local_temp):
        if p1.is_molecule or p2.is_molecule:
            return False

        key = tuple(sorted([p1.symbol, p2.symbol]))
        if key not in NORMALIZED_REACTIONS:
            return False

        rxn = NORMALIZED_REACTIONS[key]
        if not rxn["products"]:
            return False

        # Temperature-based probability modifier
        # Arrhenius-like: higher temp = higher probability
        activation_factor = math.exp(-200 / local_temp) * (local_temp / 300)
        base_prob = min(0.9, 0.2 + activation_factor * 0.3)

        min_reactants = rxn.get("min_reactants", {})
        remaining = dict(min_reactants)
        remaining[p1.symbol] = remaining.get(p1.symbol, 0) - 1
        remaining[p2.symbol] = remaining.get(p2.symbol, 0) - 1

        needed_particles = []
        for sym, count in remaining.items():
            if count > 0:
                nearby = [p for p in self.particles
                          if not p.is_molecule and p.alive and p.symbol == sym
                          and p is not p1 and p is not p2
                          and math.hypot(p.x - p1.x, p.y - p1.y) < 100]
                if len(nearby) < count:
                    return False
                needed_particles.extend(nearby[:count])

        # Probability check
        if random.random() > base_prob:
            return False

        mid_x = (p1.x + p2.x) / 2
        mid_y = (p1.y + p2.y) / 2

        p1.alive = False
        p2.alive = False
        for np in needed_particles:
            np.alive = False

        avg_vx = (p1.vx * p1.mass + p2.vx * p2.mass) / (p1.mass + p2.mass)
        avg_vy = (p1.vy * p1.mass + p2.vy * p2.mass) / (p1.mass + p2.mass)

        for mol_key, count in rxn["products"]:
            for _ in range(count):
                ox = random.uniform(-12, 12)
                oy = random.uniform(-12, 12)
                nvx = avg_vx + random.uniform(-0.5, 0.5)
                nvy = avg_vy + random.uniform(-0.5, 0.5)
                p = Particle(mid_x + ox, mid_y + oy, mol_key,
                             vx=nvx, vy=nvy, is_molecule=True, mol_key=mol_key)
                p.glow_timer = 1.2
                self.particles.append(p)

        energy = rxn["energy"]
        intensity = min(3.0, abs(energy) / 200)

        if energy < -300:
            spark_color = (255, 180, 40)
        elif energy < -100:
            spark_color = (255, 220, 80)
        elif energy < 0:
            spark_color = (200, 230, 150)
        else:
            spark_color = (80, 180, 255)

        self.sparks.append(Spark(mid_x, mid_y, spark_color, intensity))

        # Shockwave for vigorous reactions
        if abs(energy) > 400:
            sw_radius = 60 + abs(energy) / 10
            self.shockwaves.append(Shockwave(mid_x, mid_y, sw_radius, spark_color, 250))
            self.shake.trigger(min(12, abs(energy) / 50))
        elif abs(energy) > 200:
            self.shockwaves.append(Shockwave(mid_x, mid_y, 50, spark_color, 180))

        # Temperature effect from exothermic reactions
        if energy < 0:
            self.local_heat_zones.append([mid_x, mid_y, 80, abs(energy) / 10, 1.0])

        self.reaction_count += 1
        self.energy_released += abs(energy)
        self.energy_graph.add_energy(abs(energy))

        self.sound.play_reaction(energy)

        self.reaction_log.append({
            "equation": rxn["equation"],
            "energy": energy,
            "time": pygame.time.get_ticks() / 1000.0,
            "exothermic": energy < 0,
        })
        if len(self.reaction_log) > 10:
            self.reaction_log.pop(0)

        return True

    def _try_decomposition(self, particle, local_temp):
        """Try to decompose a molecule at high temperature."""
        if not particle.is_molecule or not particle.mol_key:
            return False
        mol = MOLECULE_TYPES.get(particle.mol_key)
        if not mol:
            return False
        decomp_temp = mol.get("decomp_temp", 9999)
        products = mol.get("decomp_products", [])
        if not products or local_temp < decomp_temp:
            return False

        # Probability increases with temperature above threshold
        excess = (local_temp - decomp_temp) / decomp_temp
        prob = min(0.5, excess * 2)
        if random.random() > prob:
            return False

        # Decompose!
        particle.alive = False
        for sym, count in products:
            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.5, 3.5)
                p = Particle(
                    particle.x + random.uniform(-8, 8),
                    particle.y + random.uniform(-8, 8),
                    sym,
                    vx=particle.vx + math.cos(angle) * speed,
                    vy=particle.vy + math.sin(angle) * speed,
                )
                p.glow_timer = 0.8
                self.particles.append(p)

        self.sparks.append(Spark(particle.x, particle.y, (255, 150, 50), 0.8))
        self.shockwaves.append(Shockwave(particle.x, particle.y, 30, (255, 200, 100), 150))
        self.decomp_count += 1
        self.sound.play_decomp()

        self.reaction_log.append({
            "equation": f"{mol['formula']} \u2192 {' + '.join(f'{c}{sym}' for sym, c in products)}",
            "energy": 0,
            "time": pygame.time.get_ticks() / 1000.0,
            "exothermic": False,
            "decomposition": True,
        })
        if len(self.reaction_log) > 10:
            self.reaction_log.pop(0)

        return True

    def _apply_mouse_force(self, mx, my, attract=True):
        """Apply attraction or repulsion force to nearby particles."""
        force_radius = 150
        force_strength = 0.8 if attract else -1.2
        for p in self.particles:
            if not p.alive:
                continue
            dx = mx - p.x
            dy = my - p.y
            dist = math.hypot(dx, dy)
            if 0 < dist < force_radius:
                factor = force_strength * (1 - dist / force_radius) / max(1, p.mass * 0.1)
                p.vx += (dx / dist) * factor
                p.vy += (dy / dist) * factor

    def _spawn_particle(self, x, y, vx=None, vy=None, sym=None):
        if sym is None:
            sym = self.selected_atom
        p = Particle(x, y, sym, vx=vx, vy=vy)
        self.particles.append(p)
        self.spawn_history.append(p)
        self.sound.play_spawn()
        return p

    def _delete_at(self, mx, my):
        for p in self.particles:
            if not p.alive:
                continue
            if math.hypot(p.x - mx, p.y - my) < p.radius + 5:
                p.alive = False
                self.sparks.append(Spark(p.x, p.y, (255, 80, 80), 0.5))
                return True
        return False

    def _apply_heat_zone(self, mx, my, delta):
        self.local_heat_zones.append([mx, my, 100, delta, 1.0])

    def _get_hovered(self, mx, my):
        for p in reversed(self.particles):
            if p.alive and math.hypot(p.x - mx, p.y - my) < p.radius + 3:
                return p
        return None

    def _check_collisions(self):
        alive = [p for p in self.particles if p.alive]
        n = len(alive)
        for i in range(n):
            p1 = alive[i]
            if not p1.alive:
                continue
            for j in range(i + 1, n):
                p2 = alive[j]
                if not p2.alive:
                    continue

                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dist_sq = dx * dx + dy * dy
                coll_dist = p1.radius + p2.radius

                if dist_sq < coll_dist * coll_dist:
                    dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.01
                    nx = dx / dist
                    ny = dy / dist

                    dvx = p1.vx - p2.vx
                    dvy = p1.vy - p2.vy
                    dvn = dvx * nx + dvy * ny

                    if dvn > 0:
                        m1, m2 = p1.mass, p2.mass
                        impulse = 2 * dvn / (m1 + m2)
                        p1.vx -= impulse * m2 * nx
                        p1.vy -= impulse * m2 * ny
                        p2.vx += impulse * m1 * nx
                        p2.vy += impulse * m1 * ny

                        overlap = coll_dist - dist
                        p1.x -= nx * overlap * 0.5
                        p1.y -= ny * overlap * 0.5
                        p2.x += nx * overlap * 0.5
                        p2.y += ny * overlap * 0.5

                        # Try reaction (only atom-atom)
                        if not p1.is_molecule and not p2.is_molecule:
                            mid_x = (p1.x + p2.x) / 2
                            mid_y = (p1.y + p2.y) / 2
                            local_t = self._get_effective_temperature(mid_x, mid_y)
                            self._try_reaction(p1, p2, local_t)

    def _check_decompositions(self, dt):
        for p in self.particles:
            if p.alive and p.is_molecule:
                local_t = self._get_effective_temperature(p.x, p.y)
                self._try_decomposition(p, local_t)

    def _update_heat_zones(self, dt):
        updated = []
        for zone in self.local_heat_zones:
            zone[4] -= dt * 0.5  # Decay timer
            if zone[4] > 0.01:
                updated.append(zone)
        self.local_heat_zones = updated

    def _get_bg_color(self):
        """Temperature-tinted background."""
        r, g, b = BG_BASE
        # Find closest preset
        for preset in TEMP_PRESETS:
            if self.temperature <= preset["temp"]:
                tint = preset["bg_tint"]
                return (min(255, r + tint[0]), min(255, g + tint[1]), min(255, b + tint[2]))
        return (min(255, r + 60), min(255, g + 15), min(255, b + 0))

    def _draw_sim_area(self):
        bg = self._get_bg_color()
        sim_surface = pygame.Surface((SIM_WIDTH, HEIGHT))
        sim_surface.fill(bg)

        # Grid dots
        for x in range(self.sim_rect[0] + 40, self.sim_rect[2], 40):
            for y in range(self.sim_rect[1] + 40, self.sim_rect[3], 40):
                pygame.draw.circle(sim_surface, tuple(min(255, c + 8) for c in bg), (x, y), 1)

        # Draw heat zones
        for hx, hy, hr, delta, timer in self.local_heat_zones:
            alpha = int(30 * timer)
            if delta > 0:
                color = (255, 100, 30, alpha)
            else:
                color = (30, 100, 255, alpha)
            r = int(hr * (1.5 - timer * 0.5))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (r, r), r)
            sim_surface.blit(s, (int(hx) - r, int(hy) - r))

        # Draw particles
        for p in self.particles:
            if p.alive:
                p.draw(sim_surface, self.show_structure)

        # Draw effects
        for s in self.sparks:
            s.draw(sim_surface)
        for sw in self.shockwaves:
            sw.draw(sim_surface)

        # Draw drag arrow
        if self.dragging and self.drag_start and self.drag_current:
            self._draw_launch_arrow(sim_surface)

        # Draw force field indicator
        if self.mouse_held and self.current_tool["id"] in ("attract", "repel"):
            self._draw_force_field(sim_surface)

        # Border
        rect = pygame.Rect(*self.sim_rect)
        pygame.draw.rect(sim_surface, (40, 40, 70), rect, 2, border_radius=8)

        # Apply screen shake
        ox = int(self.shake.offset_x)
        oy = int(self.shake.offset_y)
        self.screen.blit(sim_surface, (ox, oy))

    def _draw_launch_arrow(self, surface):
        sx, sy = self.drag_start
        cx, cy = self.drag_current
        dx = sx - cx
        dy = sy - cy
        length = math.hypot(dx, dy)
        if length < 5:
            return

        # Arrow line
        end_x = sx + dx * 0.5
        end_y = sy + dy * 0.5
        pygame.draw.line(surface, (255, 255, 100), (int(sx), int(sy)), (int(end_x), int(end_y)), 2)

        # Arrowhead
        angle = math.atan2(dy, dx)
        arrow_size = 10
        for da in [2.7, -2.7]:
            ax = end_x - arrow_size * math.cos(angle + da)
            ay = end_y - arrow_size * math.sin(angle + da)
            pygame.draw.line(surface, (255, 255, 100), (int(end_x), int(end_y)), (int(ax), int(ay)), 2)

        # Speed label
        speed_val = length / 30.0
        label = self.font_small.render(f"v={speed_val:.1f}", True, (255, 255, 150))
        surface.blit(label, (int(sx) + 10, int(sy) - 20))

        # Trajectory preview (dotted)
        vx = dx / 30.0
        vy = dy / 30.0
        px, py = float(sx), float(sy)
        for i in range(15):
            px += vx * 2
            py += vy * 2
            if self.gravity:
                vy += 0.15
            alpha = max(0, 150 - i * 10)
            c = (255, 255, 100)
            if i % 2 == 0:
                pygame.draw.circle(surface, c, (int(px), int(py)), 2)

    def _draw_force_field(self, surface):
        mx, my = self.mouse_pos
        is_attract = self.current_tool["id"] == "attract"
        color = (80, 150, 255) if is_attract else (255, 100, 80)
        radius = 150
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -5):
            a = int(15 * (r / radius))
            pygame.draw.circle(s, (*color, a), (radius, radius), r)
        surface.blit(s, (mx - radius, my - radius))
        # Center dot
        pygame.draw.circle(surface, color, (mx, my), 4)

    def _draw_thermometer(self, x, y, w, h):
        """Draw a thermometer showing current temperature."""
        # Background
        pygame.draw.rect(self.screen, (15, 15, 30), (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, (x, y, w, h), 1, border_radius=8)

        # Label
        label = self.font_small.render("Temperature", True, (160, 160, 200))
        self.screen.blit(label, (x + 8, y + 4))

        # Find temperature range for display
        temps = [p["temp"] for p in TEMP_PRESETS]
        min_t, max_t = 0, 3500
        fill_frac = min(1.0, max(0.0, (self.temperature - min_t) / (max_t - min_t)))

        bar_x = x + 8
        bar_y = y + 22
        bar_w = w - 16
        bar_h = h - 50

        # Gradient bar background
        for i in range(bar_h):
            frac = i / bar_h
            r = int(40 + 215 * frac)
            g = int(60 + 100 * (1 - frac))
            b = int(200 * (1 - frac))
            pygame.draw.line(self.screen, (r // 4, g // 4, b // 4),
                             (bar_x, bar_y + bar_h - i), (bar_x + bar_w, bar_y + bar_h - i))

        # Fill level
        fill_h = int(bar_h * fill_frac)
        for i in range(fill_h):
            frac = i / bar_h
            r = int(40 + 215 * frac)
            g = int(60 + 100 * (1 - frac))
            b = int(200 * (1 - frac))
            pygame.draw.line(self.screen, (r, g, b),
                             (bar_x, bar_y + bar_h - i), (bar_x + bar_w, bar_y + bar_h - i))

        pygame.draw.rect(self.screen, PANEL_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)

        # Temperature value
        temp_str = f"{self.temperature:.0f} K"
        temp_label = self.font_med.render(temp_str, True, (255, 255, 255))
        self.screen.blit(temp_label, (x + 8, y + h - 24))

        # Preset markers
        for preset in TEMP_PRESETS:
            marker_frac = (preset["temp"] - min_t) / (max_t - min_t)
            marker_y = bar_y + bar_h - int(bar_h * marker_frac)
            if bar_y <= marker_y <= bar_y + bar_h:
                pygame.draw.line(self.screen, (150, 150, 180),
                                 (bar_x + bar_w + 2, marker_y), (bar_x + bar_w + 6, marker_y), 1)

    def _draw_pressure_gauge(self, x, y, w, h):
        """Draw a simple pressure gauge."""
        alive = [p for p in self.particles if p.alive]
        if not alive:
            pressure = 0
        else:
            # P = nkT/V (simplified)
            avg_ke = sum(p.kinetic_energy() for p in alive) / len(alive)
            sim_area = (self.sim_rect[2] - self.sim_rect[0]) * (self.sim_rect[3] - self.sim_rect[1])
            pressure = len(alive) * avg_ke * self.temperature / max(1, sim_area) * 1000

        pygame.draw.rect(self.screen, (15, 15, 30), (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, PANEL_BORDER, (x, y, w, h), 1, border_radius=6)

        label = self.font_small.render("Pressure", True, (160, 160, 200))
        self.screen.blit(label, (x + 8, y + 4))

        # Bar
        bar_x = x + 8
        bar_y = y + 22
        bar_w = w - 16
        bar_h = 12

        pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)

        fill = min(1.0, pressure / 50.0)
        fill_w = int(bar_w * fill)
        if fill_w > 0:
            # Color: green -> yellow -> red
            if fill < 0.5:
                r = int(255 * fill * 2)
                g = 200
            else:
                r = 255
                g = int(200 * (1 - (fill - 0.5) * 2))
            pygame.draw.rect(self.screen, (r, g, 50), (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        pygame.draw.rect(self.screen, PANEL_BORDER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)

        val_label = self.font_small.render(f"{pressure:.1f} atm", True, (200, 200, 220))
        self.screen.blit(val_label, (x + 8, y + 38))

    def _draw_tool_bar(self):
        """Draw tool selection bar at bottom of panel."""
        bar_y = HEIGHT - 55
        pygame.draw.line(self.screen, PANEL_BORDER, (PANEL_X + 10, bar_y - 5), (WIDTH - 10, bar_y - 5), 1)

        for i, tool in enumerate(self.tool_modes):
            bx = PANEL_X + 15 + i * 62
            by = bar_y
            bw = 56
            bh = 45

            is_selected = (i == self.tool_index)
            bg_color = (50, 50, 90) if is_selected else (30, 30, 55)
            border = (100, 150, 255) if is_selected else (50, 50, 75)

            pygame.draw.rect(self.screen, bg_color, (bx, by, bw, bh), border_radius=6)
            pygame.draw.rect(self.screen, border, (bx, by, bw, bh), 2 if is_selected else 1, border_radius=6)

            # Icon
            icon = self.font_med.render(tool["icon"], True, (220, 220, 255) if is_selected else (140, 140, 170))
            icon_rect = icon.get_rect(center=(bx + bw // 2, by + 15))
            self.screen.blit(icon, icon_rect)

            # Name
            name = self.font_tiny.render(tool["name"], True, (180, 180, 210) if is_selected else (100, 100, 130))
            name_rect = name.get_rect(center=(bx + bw // 2, by + 34))
            self.screen.blit(name, name_rect)

    def _draw_panel(self):
        """Draw the info/control panel."""
        panel_rect = pygame.Rect(PANEL_X, 0, PANEL_WIDTH, HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, PANEL_BORDER, (PANEL_X, 0), (PANEL_X, HEIGHT), 2)

        y = 10

        # Title
        title = self.font_title.render("Chem Sim v2", True, (180, 180, 255))
        self.screen.blit(title, (PANEL_X + 12, y))
        y += 35

        # Current tool
        tool_label = self.font_small.render(
            f"Tool: {self.current_tool['name']} - {self.current_tool['desc']}",
            True, (120, 180, 255))
        self.screen.blit(tool_label, (PANEL_X + 12, y))
        y += 18

        # ── Atom Selector ──
        header = self.font_large.render("Atoms", True, (170, 170, 210))
        self.screen.blit(header, (PANEL_X + 12, y))
        y += 24

        cols = 7
        for i, (sym, info) in enumerate(ATOM_TYPES.items()):
            bx = PANEL_X + 8 + (i % cols) * 55
            by = y + (i // cols) * 38
            is_sel = (i == self.selected_index)

            btn_color = (50, 50, 95) if is_sel else (30, 30, 50)
            border_color = info["color"] if is_sel else (45, 45, 65)
            btn_rect = pygame.Rect(bx, by, 50, 33)
            pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=4)
            pygame.draw.rect(self.screen, border_color, btn_rect, 2 if is_sel else 1, border_radius=4)

            pygame.draw.circle(self.screen, info["color"], (bx + 11, by + 12), 5)
            sym_lbl = self.font_small.render(sym, True, (255, 255, 255))
            self.screen.blit(sym_lbl, (bx + 20, by + 2))
            # Show key hint only for first 10
            if i < 10:
                key_str = str(i + 1 if i < 9 else 0)
            else:
                key_str = ""
            if key_str:
                key_lbl = self.font_tiny.render(f"[{key_str}]", True, (90, 90, 120))
                self.screen.blit(key_lbl, (bx + 20, by + 19))

        y += (len(ATOM_TYPES) // cols + 1) * 38 + 3

        # ── Stats ──
        alive = [p for p in self.particles if p.alive]
        atoms = [p for p in alive if not p.is_molecule]
        molecules = [p for p in alive if p.is_molecule]

        stats = [
            f"Atoms: {len(atoms)}  Mol: {len(molecules)}  Total: {len(alive)}",
            f"Reactions: {self.reaction_count}  Decomp: {self.decomp_count}",
        ]
        for s in stats:
            lbl = self.font_small.render(s, True, (150, 150, 180))
            self.screen.blit(lbl, (PANEL_X + 12, y))
            y += 16

        y += 4

        # ── Energy Graph ──
        self.energy_graph.y = y
        self.energy_graph.x = PANEL_X + 10
        self.energy_graph.w = PANEL_WIDTH - 20
        self.energy_graph.draw(self.screen, self.font_small)
        y += self.energy_graph.h + 8

        # ── Thermometer & Pressure ──
        self._draw_thermometer(PANEL_X + 10, y, (PANEL_WIDTH - 25) // 2, 90)
        self._draw_pressure_gauge(PANEL_X + (PANEL_WIDTH + 5) // 2, y, (PANEL_WIDTH - 25) // 2, 55)
        y += 96

        # ── Inventory ──
        header = self.font_large.render("Inventory", True, (170, 170, 210))
        self.screen.blit(header, (PANEL_X + 12, y))
        y += 22

        atom_counts = {}
        for p in atoms:
            atom_counts[p.symbol] = atom_counts.get(p.symbol, 0) + 1
        mol_counts = {}
        for p in molecules:
            key = p.mol_key or p.symbol
            mol_counts[key] = mol_counts.get(key, 0) + 1

        inv_y = y
        col2_x = PANEL_X + PANEL_WIDTH // 2

        for sym, count in sorted(atom_counts.items(), key=lambda x: -x[1]):
            info = ATOM_TYPES[sym]
            pygame.draw.circle(self.screen, info["color"], (PANEL_X + 22, inv_y + 7), 5)
            lbl = self.font_tiny.render(f"{sym}: {count}", True, (150, 150, 180))
            self.screen.blit(lbl, (PANEL_X + 34, inv_y))
            inv_y += 16

        inv_y2 = y
        for key, count in sorted(mol_counts.items(), key=lambda x: -x[1]):
            info = MOLECULE_TYPES.get(key, {})
            color = info.get("color", (180, 180, 180))
            pygame.draw.circle(self.screen, color, (col2_x, inv_y2 + 7), 5)
            formula = info.get("formula", key)
            lbl = self.font_tiny.render(f"{formula}: {count}", True, (150, 150, 180))
            self.screen.blit(lbl, (col2_x + 12, inv_y2))
            inv_y2 += 16

        y = max(inv_y, inv_y2) + 6

        # ── Reaction Log ──
        header = self.font_large.render("Log", True, (170, 170, 210))
        self.screen.blit(header, (PANEL_X + 12, y))
        y += 22

        available_height = HEIGHT - 55 - y - 5  # Leave room for toolbar
        max_entries = max(1, available_height // 30)

        for entry in reversed(self.reaction_log[-max_entries:]):
            if y > HEIGHT - 65:
                break
            is_decomp = entry.get("decomposition", False)
            if is_decomp:
                color = (255, 200, 80)
            elif entry["exothermic"]:
                color = (255, 170, 70)
            else:
                color = (80, 180, 255)
            eq = self.font_tiny.render(entry["equation"], True, color)
            self.screen.blit(eq, (PANEL_X + 12, y))
            energy_str = f"{'Exo' if entry['exothermic'] else 'Endo'}: {abs(entry['energy'])} kJ/mol" if entry["energy"] != 0 else "Decomposition"
            en = self.font_tiny.render(energy_str, True, (100, 100, 130))
            self.screen.blit(en, (PANEL_X + 12, y + 13))
            y += 28

        # ── Tool Bar ──
        self._draw_tool_bar()

        # ── Status bar ──
        status_y = HEIGHT - 12
        parts = []
        if self.paused:
            parts.append(("PAUSED", (255, 100, 100)))
        parts.append((f"Speed: {self.speed_mult:.1f}x", (140, 140, 170)))
        if self.gravity:
            parts.append(("Gravity", (100, 200, 100)))
        parts.append((f"Sound: {'ON' if self.sound.enabled else 'OFF'}", (140, 140, 170)))
        sx = PANEL_X + 12
        for text, color in parts:
            lbl = self.font_tiny.render(text, True, color)
            self.screen.blit(lbl, (sx, status_y))
            sx += lbl.get_width() + 12

    def _draw_tooltip(self):
        if not self.hovered_particle:
            return
        p = self.hovered_particle
        if not p.alive:
            self.hovered_particle = None
            return

        lines = []
        if p.is_molecule:
            mol = MOLECULE_TYPES.get(p.mol_key, {})
            lines.append(f"{p.formula} (molecule)")
            lines.append(f"Mass: {p.mass} u")
            dt = mol.get("decomp_temp", 9999)
            lines.append(f"Decomp: {dt} K")
            if dt <= self.temperature:
                lines.append("!! Unstable at current T !!")
        else:
            info = ATOM_TYPES[p.symbol]
            lines.append(f"{info['name']} ({p.symbol})")
            lines.append(f"Mass: {p.mass} u  Valence: {info['valence']}")
            lines.append(f"Group: {info['group']}  e-: {info['electrons']}")

        local_t = self._get_effective_temperature(p.x, p.y)
        lines.append(f"Speed: {p.speed():.1f}  KE: {p.kinetic_energy():.1f}")
        lines.append(f"Local T: {local_t:.0f} K")

        mx, my = pygame.mouse.get_pos()
        padding = 6
        line_h = 16
        max_w = max(self.font_tiny.size(l)[0] for l in lines) + padding * 2
        total_h = len(lines) * line_h + padding * 2

        tx = min(mx + 15, WIDTH - max_w - 5)
        ty = min(my + 15, HEIGHT - total_h - 5)

        s = pygame.Surface((max_w, total_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 50, 220), (0, 0, max_w, total_h), border_radius=5)
        pygame.draw.rect(s, (80, 80, 140, 200), (0, 0, max_w, total_h), 1, border_radius=5)

        for i, line in enumerate(lines):
            color = (255, 200, 100) if "!!" in line else (200, 200, 230)
            lbl = self.font_tiny.render(line, True, color)
            s.blit(lbl, (padding, padding + i * line_h))

        self.screen.blit(s, (tx, ty))

    def _draw_cursor_preview(self):
        """Draw cursor preview for spawn tool."""
        mx, my = pygame.mouse.get_pos()
        if mx >= SIM_WIDTH:
            return
        if self.current_tool["id"] == "spawn":
            info = ATOM_TYPES[self.selected_atom]
            r = info["radius"]
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*info["color"], 70), (r + 2, r + 2), r)
            self.screen.blit(s, (mx - r - 2, my - r - 2))
        elif self.current_tool["id"] == "heat":
            s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 100, 30, 50), (20, 20), 20)
            self.screen.blit(s, (mx - 20, my - 20))
        elif self.current_tool["id"] == "cool":
            s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(s, (30, 100, 255, 50), (20, 20), 20)
            self.screen.blit(s, (mx - 20, my - 20))
        elif self.current_tool["id"] == "delete":
            s = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.line(s, (255, 80, 80, 180), (4, 4), (20, 20), 2)
            pygame.draw.line(s, (255, 80, 80, 180), (20, 4), (4, 20), 2)
            self.screen.blit(s, (mx - 12, my - 12))

    def _take_screenshot(self):
        self.screenshot_count += 1
        filename = f"/home/z/my-project/download/chem_sim_{self.screenshot_count}.png"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        pygame.image.save(self.screen, filename)
        self.reaction_log.append({
            "equation": f"Screenshot saved",
            "energy": 0,
            "time": pygame.time.get_ticks() / 1000.0,
            "exothermic": False,
        })
        print(f"Screenshot saved: {filename}")

    def _undo_spawn(self):
        if self.spawn_history:
            p = self.spawn_history.pop()
            if p.alive:
                p.alive = False
                self.sound.play_decomp()

    def reset(self):
        self.particles.clear()
        self.sparks.clear()
        self.shockwaves.clear()
        self.local_heat_zones.clear()
        self.reaction_count = 0
        self.energy_released = 0
        self.decomp_count = 0
        self.reaction_log.clear()
        self.spawn_history.clear()
        self.energy_graph = EnergyGraph(PANEL_X + 10, 0, PANEL_WIDTH - 20, 90)
        self._spawn_initial()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_g:
                    self.gravity = not self.gravity
                elif event.key == pygame.K_b:
                    self.show_structure = not self.show_structure
                elif event.key == pygame.K_m:
                    self.sound.toggle()
                elif event.key == pygame.K_t:
                    self.temp_preset_idx = (self.temp_preset_idx + 1) % len(TEMP_PRESETS)
                    self.temperature = TEMP_PRESETS[self.temp_preset_idx]["temp"]
                elif event.key == pygame.K_h:
                    mx, my = pygame.mouse.get_pos()
                    self._apply_heat_zone(mx, my, 300)
                elif event.key == pygame.K_j:
                    mx, my = pygame.mouse.get_pos()
                    self._apply_heat_zone(mx, my, -300)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.speed_mult = min(5.0, self.speed_mult + 0.25)
                elif event.key == pygame.K_MINUS:
                    self.speed_mult = max(0.25, self.speed_mult - 0.25)
                elif event.key == pygame.K_TAB or event.key == pygame.K_q:
                    self.tool_index = (self.tool_index - 1) % len(self.tool_modes)
                    self.current_tool = self.tool_modes[self.tool_index]
                elif event.key == pygame.K_w and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.tool_index = (self.tool_index + 1) % len(self.tool_modes)
                    self.current_tool = self.tool_modes[self.tool_index]
                elif event.key == pygame.K_F12:
                    self._take_screenshot()
                elif event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self._undo_spawn()
                # Shift+1..9,0 for elements 11-20 (check BEFORE plain digits)
                elif (pygame.K_1 <= event.key <= pygame.K_9) and (mods & pygame.KMOD_SHIFT):
                    idx = 10 + (event.key - pygame.K_1)
                    if idx < len(self.atom_keys):
                        self.selected_index = idx
                        self.selected_atom = self.atom_keys[idx]
                elif event.key == pygame.K_0 and (mods & pygame.KMOD_SHIFT):
                    if len(self.atom_keys) >= 20:
                        self.selected_index = 19
                        self.selected_atom = self.atom_keys[19]
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(self.atom_keys):
                        self.selected_index = idx
                        self.selected_atom = self.atom_keys[idx]
                elif event.key == pygame.K_0:
                    if len(self.atom_keys) >= 10:
                        self.selected_index = 9
                        self.selected_atom = self.atom_keys[9]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                mods = pygame.key.get_mods()

                if event.button == 1:  # Left click
                    if mx < SIM_WIDTH:
                        tool = self.current_tool["id"]
                        if tool == "spawn":
                            if mods & pygame.KMOD_SHIFT:
                                self.emitting = True
                                self.emit_timer = 0
                            else:
                                self.dragging = True
                                self.drag_start = (mx, my)
                                self.drag_current = (mx, my)
                        elif tool in ("attract", "repel"):
                            self.mouse_held = True
                            self.mouse_pos = (mx, my)
                        elif tool == "heat":
                            self._apply_heat_zone(mx, my, 400)
                        elif tool == "cool":
                            self._apply_heat_zone(mx, my, -400)
                        elif tool == "delete":
                            self._delete_at(mx, my)

                elif event.button == 3:  # Right click - quick spawn
                    if mx < SIM_WIDTH:
                        sym = random.choice(self.atom_keys)
                        self._spawn_particle(mx, my, sym=sym)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mx, my = event.pos
                    if self.dragging and self.drag_start:
                        sx, sy = self.drag_start
                        dx = sx - mx
                        dy = sy - my
                        vx = dx / 30.0
                        vy = dy / 30.0
                        self._spawn_particle(sx, sy, vx=vx, vy=vy)
                        self.dragging = False
                        self.drag_start = None
                        self.drag_current = None
                    if self.emitting:
                        self.emitting = False
                    if self.mouse_held:
                        self.mouse_held = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if self.dragging:
                    self.drag_current = (mx, my)
                if self.mouse_held:
                    self.mouse_pos = (mx, my)
                # Hover detection
                if mx < SIM_WIDTH:
                    self.hovered_particle = self._get_hovered(mx, my)
                else:
                    self.hovered_particle = None

        return True

    def update(self, dt):
        if self.paused:
            return

        # Continuous emitter
        if self.emitting:
            self.emit_timer += dt
            if self.emit_timer > 0.08:
                self.emit_timer = 0
                mx, my = pygame.mouse.get_pos()
                if mx < SIM_WIDTH:
                    vx = random.uniform(-1, 1)
                    vy = random.uniform(-2, 0)
                    self._spawn_particle(mx + random.uniform(-10, 10), my, vx=vx, vy=vy)

        # Mouse force
        if self.mouse_held and self.mouse_pos[0] < SIM_WIDTH:
            is_attract = self.current_tool["id"] == "attract"
            self._apply_mouse_force(self.mouse_pos[0], self.mouse_pos[1], attract=is_attract)

        # Update particles
        for p in self.particles:
            if p.alive:
                local_t = self._get_effective_temperature(p.x, p.y)
                p.update(dt, self.speed_mult, self.gravity, self.sim_rect, local_t)

        # Collisions & reactions
        self._check_collisions()

        # Decompositions
        self._check_decompositions(dt)

        # Update effects
        for s in self.sparks:
            s.update(dt)
        for sw in self.shockwaves:
            sw.update(dt)
        self._update_heat_zones(dt)
        self.shake.update(dt)

        # Clean up
        self.particles = [p for p in self.particles if p.alive]
        self.sparks = [s for s in self.sparks if s.alive]
        self.shockwaves = [sw for sw in self.shockwaves if sw.alive]

        # Cap particles for performance
        if len(self.particles) > 500:
            # Remove oldest molecules first
            molecules = [p for p in self.particles if p.is_molecule]
            atoms = [p for p in self.particles if not p.is_molecule]
            if molecules:
                excess = len(self.particles) - 400
                for p in molecules[:excess]:
                    p.alive = False
                self.particles = [p for p in self.particles if p.alive]

    def draw(self):
        self.screen.fill(BG_BASE)
        self._draw_sim_area()
        self._draw_panel()
        self._draw_tooltip()
        self._draw_cursor_preview()

        # Particle count cap warning
        if len(self.particles) > 400:
            warn = self.font_small.render(f"Particle cap: {len(self.particles)}/500", True, (255, 200, 80))
            self.screen.blit(warn, (15, HEIGHT - 25))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            running = self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sim = ChemicalSimulation()
    sim.run()