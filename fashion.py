#!/usr/bin/env python3

SATsolver = r"C:\Users\FAITH\Downloads\z3-4.14.1-x64-win\z3-4.14.1-x64-win\bin\z3.exe"

import sys
from subprocess import Popen, PIPE
from itertools import combinations

# Data structures for garments and colors
garments = {}
colors = set()

# Constraints configuration
MIN_G, MAX_G = 3, 6
MIN_C, MAX_C = 2, 4
color_clashes = [("red", "pink")]
layering = [("coat", "top")]
one_per_body_part = ["hat", "coat", "top", "bottom", "shoes", "gloves"]

# SAT variables and mappings
gVarNumberToName = ["invalid"]
gVarNameToNumber = {}

# Helper functions
def varCount():
    return len(gVarNumberToName) - 1

def varNameToNumber(name):
    return gVarNameToNumber[name]

def addVarName(name):
    gVarNumberToName.append(name)
    gVarNameToNumber[name] = varCount()

def getVarName(garment, color):
    return f"{garment}_{color}"

def genVarNames():
    for garment in garments:
        for color in garments[garment]:
            addVarName(getVarName(garment, color))

def genClauses():
    WINTER = True
    # Preferences (for simulating soft constraints)
    # Prefer (preferred_item) over (dispreferred_item)
    preferences = [
        (("gloves", "black"), ("gloves", "white")),
        (("coat", "blue"), ("coat", "red")),
        (("top", "black"), ("top", "green"))
    ]
    clauses = []

    # A: Outfit size constraints (MIN_G to MAX_G)
    all_vars = [varNameToNumber(getVarName(g, c)) for g in garments for c in garments[g]]

    clauses.append(all_vars)  # At least one garment
    for comb in combinations(all_vars, MAX_G + 1):  # At most MAX_G garments
        clauses.append([-x for x in comb])

    # At least MIN_G garments
    for comb in combinations(all_vars, len(all_vars) - MIN_G + 1):
        clauses.append([x for x in comb])

    # B: Type Coverage (at least one garment per type)
    for garment_type in garments:
        clauses.append([varNameToNumber(getVarName(garment_type, c)) for c in garments[garment_type]])

    # C: Palette size constraints
    color_vars = {}
    for color in colors:
        color_vars[color] = [varNameToNumber(getVarName(g, color)) for g in garments if color in garments[g]]

    # At least MIN_C colors
    clauses.append([var for color_group in color_vars.values() for var in color_group])

    # At most MAX_C colors
    for comb in combinations(colors, MAX_C + 1):
        color_comb_vars = [var for color in comb for var in color_vars[color]]
        clauses.append([-var for var in color_comb_vars])

    # D: Color Clashes
    for c1, c2 in color_clashes:
        for g1 in garments:
            if c1 in garments[g1]:
                for g2 in garments:
                    if c2 in garments[g2]:
                        clauses.append([-varNameToNumber(getVarName(g1, c1)), -varNameToNumber(getVarName(g2, c2))])

    # E: Complement Harmony – if warm colors are worn, at least one cool color must also appear
    warm_colors = {"red", "orange", "yellow"}
    cool_colors = {"blue", "green", "cyan"}

    print("\n=== Checking Complement Harmony Constraint ===")
    for warm in warm_colors:
        warm_vars = [varNameToNumber(getVarName(g, warm))
                    for g in garments if warm in garments[g]]

        if not warm_vars:
            print(f"[SKIP] No garments found in warm color '{warm}'")
            continue
        else:
            print(f"[WARM] {warm} → variables: {[gVarNumberToName[v] for v in warm_vars]}")

        cool_vars = []
        for cool in cool_colors:
            for g in garments:
                if cool in garments[g]:
                    cool_vars.append(varNameToNumber(getVarName(g, cool)))

        if cool_vars:
            print(f"[COOL OPTIONS] Found cool garments: {[gVarNumberToName[v] for v in cool_vars]}")
        else:
            print("[BLOCKING] No cool colors available → all warm items will be blocked.")

        for wv in warm_vars:
            clause = [-wv] + cool_vars
            print("Adding clause:", clause, "==>", "¬" + gVarNumberToName[wv], "or", [gVarNumberToName[v] for v in cool_vars])
            clauses.append(clause)


    # F: Layering Order
    for upper, lower in layering:
        if upper in garments and lower in garments:
            for upper_color in garments[upper]:
                clauses.append([-varNameToNumber(getVarName(upper, upper_color))] + [varNameToNumber(getVarName(lower, lower_color)) for lower_color in garments[lower]])

    # G: One-Per-Body-Part
    for part in one_per_body_part:
        if part in garments:
            part_vars = [varNameToNumber(getVarName(part, c)) for c in garments[part]]
            for comb in combinations(part_vars, 2):
                clauses.append([-x for x in comb])
    # H: Season / Context → if WINTER, require coat or gloves
    if WINTER:
        outerwear_vars = []
        for part in ["coat", "gloves"]:
            if part in garments:
                outerwear_vars += [varNameToNumber(getVarName(part, c)) for c in garments[part]]

        if outerwear_vars:
            print("[WINTER] Adding requirement: at least one of coat or gloves must be worn.")
            print("Clause:", outerwear_vars)
            clauses.append(outerwear_vars)
        else:
            print("[WINTER] No outerwear (coat/gloves) available → outfit is UNSAT by default.")
            clauses.append([])  # Adds empty clause = UNSAT 

    # I: Cost / Style Preference Simulation (soft constraints via implication)
    for (preferred, less_preferred) in preferences:
        g1, c1 = preferred
        g2, c2 = less_preferred
        if g1 in garments and c1 in garments[g1] and g2 in garments and c2 in garments[g2]:
            v1 = varNameToNumber(getVarName(g1, c1))  # preferred
            v2 = varNameToNumber(getVarName(g2, c2))  # less preferred

            # Prefer v1 over v2: if v2 is selected, v1 should be too
            # This clause: ¬v2 ∨ v1
            clauses.append([-v2, v1])
            print(f"[Preference] Prefer {g1}_{c1} over {g2}_{c2} → Clause: [-{v2}, {v1}]")
                           

    return clauses

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: script.py <input_file>")
        sys.exit(1)

    with open(sys.argv[1]) as file:
        for line in file:
            garment, color = line.strip().split()
            colors.add(color)
            garments.setdefault(garment, set()).add(color)

    genVarNames()
    clauses = genClauses()

    header = f"p cnf {varCount()} {len(clauses)}\n"
    cnf = "\n".join([" ".join(map(str, clause)) + " 0" for clause in clauses])

    with open("tmp_prob.cnf", "w") as f:
        f.write(header + cnf)

    solverOutput = Popen([SATsolver, "tmp_prob.cnf"], stdout=PIPE).communicate()[0]
    res = solverOutput.decode('utf-8')
    print(res)

    # Parse result and print selected garments
if res.startswith("s SATISFIABLE"):
    lines = res.strip().split("\n")
    model_line = next((line for line in lines if line.startswith("v ")), None)
    if model_line:
        selected_vars = list(map(int, model_line.split()[1:]))  # skip "v"
        selected_vars = [v for v in selected_vars if v > 0]     # only true variables

        print("\nSelected garments:")
        for var in selected_vars:
            if var < len(gVarNumberToName):
                print(" -", gVarNumberToName[var])
