import pandas as pd
from datetime import datetime
import re

# Parse quantity like "2 kg" or "500 ml"
def parse_quantity(qty_string):
    match = re.match(r"([\d\.]+)\s*(\w+)", str(qty_string).lower())
    return (float(match.group(1)), match.group(2)) if match else (None, None)

# Standardize to grams/ml or pieces
def standardize_quantity(quantity, unit):
    if unit == 'kg': return quantity * 1000
    if unit == 'g': return quantity
    if unit == 'l': return quantity * 1000
    if unit == 'ml': return quantity
    if unit in ['pcs', 'piece', 'pieces']: return quantity
    return None

# Process and filter inventory data
def filter_valid_ingredients(inventory_df):
    today = datetime.now()
    inventory_df['Expiry Date'] = pd.to_datetime(inventory_df['Expiry Date'], dayfirst=True)

    parsed = inventory_df['Quantity'].apply(parse_quantity)
    inventory_df['value'] = parsed.apply(lambda x: x[0])
    inventory_df['unit'] = parsed.apply(lambda x: x[1])
    inventory_df['standardized_quantity'] = inventory_df.apply(lambda row: standardize_quantity(row['value'], row['unit']), axis=1)

    valid_df = inventory_df[(inventory_df['Expiry Date'] > today) & (inventory_df['standardized_quantity'] > 0)]
    return valid_df['Ingredient'].str.lower().tolist()

# Find dishes that can be made from valid ingredients
def find_possible_dishes(menu_df, available_ingredients):
    possible = []
    for _, row in menu_df.iterrows():
        required = [i.strip().lower() for i in row['ingredients'].split(',')]
        if all(i in available_ingredients for i in required):
            possible.append(row['name'])
    return possible
