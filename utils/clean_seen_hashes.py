import json
import os

def clean_seen_hashes(file_path="seen_hashes.json", keep_last=500):
    if not os.path.exists(file_path):
        print("⚠️ No seen hashes file found.")
        return
    
    with open(file_path, "r") as f:
        hashes = json.load(f)  # This is a dict
    
    if len(hashes) > keep_last:
        # Keep only the last N entries based on insertion order
        hashes = dict(list(hashes.items())[-keep_last:])
        with open(file_path, "w") as f:
            json.dump(hashes, f, indent=2)
        print(f"✅ Cleaned seen hashes file. Kept last {keep_last} entries.")
    else:
        print("ℹ️ No cleaning needed.")

if __name__ == "__main__":
    clean_seen_hashes("seen_hashes.json", keep_last=500)
