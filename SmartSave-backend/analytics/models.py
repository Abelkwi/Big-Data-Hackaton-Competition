from django.db import models

# Analytics uses database-level aggregations from other apps.
# No dedicated models needed - data is queried live from
# accounts, marketplace, orders, and other apps.