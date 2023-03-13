Inventory module describes abstrations any SoT must support.

Injventory class must implement the following protocol:
::: napi.inventory

## New SoT
If you wish to add new SoT support to the `napi` after you describe you inventory class
you must import your class into `inventory/__init__.py` and add it to the `inventory_map` map.
