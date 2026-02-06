import json

# Load file
with open('examples/SubTest1.rsim', 'r') as f:
    data = json.load(f)

# Save back (this will fix any formatting and the leading space will be removed manually in next step)
with open('examples/SubTest1.rsim', 'w') as f:
    json.dump(data, f, indent=2)

print("File re-serialized successfully")
