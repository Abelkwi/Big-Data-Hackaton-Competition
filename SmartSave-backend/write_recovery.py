import os

BASE = r"c:\Users\user\OneDrive\Desktop\Website\smartsave-backend\recovery"

# 1. models.py
models = open(os.path.join(BASE, "models.py"), "r").read()  # already written
print("models.py already has content, size:", len(models))

# Let\'s check what we have
for fn in ["models.py","serializers.py","api_views.py","api_urls.py","admin.py"]:
    p = os.path.join(BASE, fn)
    if os.path.exists(p):
        sz = os.path.getsize(p)
        print(f"{fn}: {sz} bytes")
    else:
        print(f"{fn}: MISSING")
