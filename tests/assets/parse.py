import json, sys
from playwright.sync_api import sync_playwright
METHOD = """🧑‍🍳 Method
1️⃣ Combine the smoked paprika, cumin,
chilli powder, oregano, salt and black pepper.
2️⃣ Rub the spice mixture generously all over
the pork tenderloin.
3️⃣ Add the sliced red onion and minced
garlic to the slow cooker. Place the seasoned
pork on top.
4️⃣ Mix together the orange juice, lime juice,
chicken stock and tomato purée. Pour around
the pork.
5️⃣ Cook on LOW for around 4 hours,
checking towards the end. Pork tenderloin is
lean, so avoid overcooking.
6️⃣ Check the pork has reached a safe
internal temperature, then remove and rest
for 5-10 minutes.
7️⃣ While the pork rests, transfer the cooking
liquid to a saucepan. Mix the cornflour with a
little cold water to make a slurry, stir into the
sauce and simmer for a few minutes until
slightly thickened.
8️⃣ Shred or thinly slice the pork and toss
with some of the thickened sauce."""
FULL = """Slow Cooker Mexican Pulled Pork Tacos 🌮🔥 Only 6 syns!
Serves 4 | 450 kcal per serving
🛒 Ingredients
- 500g pork tenderloin
- 1 red onion, sliced
- 3 garlic cloves, minced
- 2 tsp smoked paprika
- 1 tsp cumin
- 1 tsp chilli powder
- 1 tsp dried oregano
- Salt and black pepper
- Juice of 1 orange
- Juice of 1 lime
- 150ml chicken stock
- 1 tbsp tomato purée
- 1 tbsp cornflour
- 8 mini tortilla wraps
- Shredded lettuce
- 2 tomatoes, diced
- 1 avocado (optional)
- Fresh coriander, to serve
- Optional: Tex Mex dips
🧑‍🍳 Method
""" + METHOD.split('\n',1)[1] + "\nFollow @slimming.gym.and.gin for more! #slimmingworld #fakeaway"
ONELINE = "Ingredients: 500g beef mince, 1 onion, 2 cloves garlic, 1 tin chopped tomatoes, 1 tin kidney beans, 2 tsp chilli powder"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto('http://localhost:8765/'); pg.wait_for_timeout(500)
    for nm, t in (('METHOD', METHOD), ('FULL', FULL), ('ONELINE', ONELINE)):
        r = pg.evaluate("t => parseIngredients(t)", t)
        print(nm, r['mode']); [print('   ', ('[x]' if x['on'] else '[ ]'), x['name'], ('x%d' % x['qty']) if x['qty'] > 1 else '') for x in r['rows']]
    b.close()
