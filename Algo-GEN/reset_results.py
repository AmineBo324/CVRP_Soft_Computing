import os
import json

files_to_delete = ['all_results.json', 'result.json', 'best_result.json']

for file in files_to_delete:
    if os.path.exists(file):
        os.remove(file)
        print(f"🗑️  Supprimé: {file}")
    else:
        print(f"⚠️  Pas trouvé: {file}")

print("\n✅ Résultats réinitialisés!")