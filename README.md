# Virtual Trolley

A shopping list with a tab for each shop. It works with no signal, has no ads, and lists can be shared live with family. Nobody needs an account.

Live at **https://list-sharing.web.app**

## Using it

- **Add**: type in the box at the top. About 2,400 UK groceries are built in, and spelling mistakes are fine ("origano" finds Oregano). Things you've added before rank first. Add a quantity with "Chicken x4" or "4x chicken".
- **Shops**: tap **+ Add** at the end of the tabs. Supermarkets start with 24 aisles in walking order (Fruit & veg, Bakery, Meat & poultry, Fish & seafood, Dairy & eggs, Cheese, Chilled & deli, Frozen, Herbs & spices, Pasta, rice & grains, Tins & jars, Sauces & condiments, Baking, Breakfast & spreads, Tea & coffee, World foods, Snacks & sweets, Soft drinks, Beer, wine & spirits, Household, Toiletries & beauty, Health & medicine, Baby, Pets). Items file themselves into the right aisle. Any other shop, and every shared list, gets aisles on its own as things are added. The List tab groups by aisle too. Empty aisles stay hidden, and an aisle you delete stays deleted. To delete an aisle, open the shop's settings and slide it to the left, then tap Delete.
- **Move things around**: hold an item to send it to another shop, change its aisle or quantity, rename it or remove it. Hold the handle on the right for a moment, then drag to reorder. Whatever you change is remembered next time.
- **Tick off**: tap an item and it drops into the trolley at the bottom of the screen. Swipe up on the trolley (or tap it) to see what's in it. Tap anything you put back to return it to the list. **Empty the trolley** clears it when you've finished. It needs two taps, and there's an Undo.
- **Tabs at the top**: Settings > **Tabs at the top**, or long-press the List tab. Switch any tab off, including List, and reorder the rest. Hidden shops keep their items and still appear when you hold an item to send it somewhere.
- **Due again**: after something has been bought twice, the app learns how often you buy it and suggests it when it's due.
- **Older shops**: a shop made before version 2.0 shows **Update to the new aisles** in its ••• menu. Items you filed yourself stay where they are.
- **Undo**: every move, removal or clear has an Undo button for 6 seconds. Settings > Recently removed has the rest.

## Sharing a list

- **Create**: **+ Add** > **New shared list**. Shared tabs show a small cloud.
- **Share a list you already have**: open it and tap the Share button (or its settings), then **Share this list live**. It keeps its tab, items and aisles, and gets a code to share.
- **Share it**: open the list, tap **•••** > **Share code**. It shows a QR code and a code like `TRLY-7K2M-Q9RD-4XNP-W8TA`.
- **Join, in the same room**: on the other phone, **+ Add** > **Join a shared list** > **Scan their code**. Scan from inside the app, not with the Camera app, because iPhone opens Camera links in Safari.
- **Join from a message**: the **Send** button writes a message containing the code. The other person copies the whole message, then taps **+ Add** > **Join a shared list** > **Paste a code**.

On shared lists, things other people added show their name in small grey letters, and anything added on another phone since you last opened the app has a small **New** tag. Your name is set from the prompt at the top of a shared list, or in Settings.

Changes appear on the other phones within a second or two. With no signal, changes wait and send later.

## Moving lists to another phone, or from the old address

The old address (danyoung1190.github.io/basket) shows **Virtual Trolley has a new home** with a **Move my lists** button. Moving takes about a minute:

1. In the old app, tap **Move my lists**. It copies a code like `MOVE-XXXX-XXXX-XXXX-XXXX`.
2. Open **list-sharing.web.app** in Safari and add it to your Home Screen (Share > Add to Home Screen).
3. Open the new app. On the welcome screen choose **Moving from another phone or the old app**, then tap **Paste**.

Everything comes across: private shops, hidden tabs, history and shared lists. The same thing works between two phones (Settings > Send my lists, then Settings > Bring lists on the other phone). A code works once and lasts 7 days.

## Setup (already done, kept here for reference)

**Hosting.** Every commit to `main` deploys to Firebase Hosting through `.github/workflows/deploy.yml`, using the repository secret `FIREBASE_SERVICE_ACCOUNT` (a private key from Firebase > Project settings > Service accounts). The site name is set in `firebase.json`. GitHub Pages still serves the old address from the same files, and that's what shows the "new home" banner.

**Firebase.** Project `shopping-list-8c011`, with Anonymous sign-in enabled and the Firestore rules from `firestore.rules` pasted into Firestore > Rules > Publish. The rules need the `transfers` section for moving lists. `firebase-config.js` holds the web app config. Those values identify the project and are not secret.

**Releasing a change.** Edit the files, change `CACHE` in `sw.js` (for example `trolley-v13`), and commit. Phones pick up the new version the next time the app opens with signal, sometimes after closing and reopening it once. Settings shows the version number at the bottom.

## Things to know

- **Private lists live on the phone.** Deleting the Home Screen icon deletes them. Back up now and then (Settings > Back up now), or use a move code.
- **Each web address keeps its own storage on iPhone**, so changing the address later means moving lists again.
