import json

input_file = './ingredients.json'
output_file = './ingredients_data.json'

with open(input_file, 'r', encoding='utf-8') as f:
    ingredients = json.load(f)


fixture = []
for idx, ingredient in enumerate(ingredients, start=1000):
    fixture.append({
        "model": "recipes.Ingredient",
        "pk": idx,
        "fields": {
            "name": ingredient["name"],
            "measurement_unit": ingredient["measurement_unit"],
            "created_at": "2025-04-01T10:00:00Z",
            "updated_at": "2025-04-01T10:00:00Z"
        }
    })

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(fixture, f, ensure_ascii=False, indent=4)

print(f"Fixture file '{output_file}' has been created successfully.")
