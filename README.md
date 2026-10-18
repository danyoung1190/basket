# Basket: setup

A private, ad-free shopping list that works offline. Everything is saved on the phone itself. There are no accounts and no servers to run.

## 1. Put it online (free, about 5 minutes)

It needs an https web address so the iPhone can install it and use it offline. GitHub Pages is free:

1. Sign in at github.com and create a new **public** repository, for example `basket`.
2. Click **Add file > Upload files** and drag in everything from this folder, including the `icons` folder. Then commit.
3. Go to **Settings > Pages**. Under **Branch**, choose `main` and `/ (root)`, then click Save.
4. After about a minute, the site will be at `https://YOUR-USERNAME.github.io/basket/`

## 2. Install it on her iPhone (the app also shows these steps when opened in Safari)

1. Open that address in **Safari**. It must be Safari.
2. Tap **Share > Add to Home Screen > Add**.
3. Open Basket from the Home Screen icon from then on, not from Safari. The two keep separate lists.

## How she uses it

- **Add**: type in the box, or tap a suggestion. Around 780 common UK groceries are built in, so suggestions appear from the first letters. Things she adds herself rank first.
- **Quantities**: type "Chicken x4" or "4x chicken", or hold an item and use − / +. Tapping a suggestion reuses the quantity she last used.
- **Sections**: new shops come with Fruit & veg, Bakery, Meat & fish, Fridge, Freezer, Cupboard and others. Items file themselves into the right one. If she moves something, that choice is remembered over the built-in guess. Empty sections stay hidden until she drags an item.
- **Due again**: each tick-off is recorded as a purchase. Once something has been bought twice or more, the app learns how often she buys it and shows it under "Due again" when it's due. Holding an item shows its history, for example "Bought 5 times, about every 7 days".
- **Send to a shop**: hold an item, then tap a shop. "Send N to their usual shops" sorts everything she has sent somewhere before.
- **Reorder**: drag the handle on the right of an item. Drag it under a section heading, such as Fridge, to file it there.
- **Tick off**: tap an item. Ticked items go grey at the bottom. Tap **Clear** when she has finished shopping.
- **Shop settings** (the ... button, or hold a shop's tab): rename it, change its colour, and add sections in the order she walks round the shop.
- **Share**: the share button sends the list as text, for example to WhatsApp.
- **Undo**: every move, removal or clear shows an Undo button for 6 seconds.
- **Recently removed**: open Settings to restore anything that was removed or cleared.

## Important things to know

- **The list lives only on her phone.** Deleting the Home Screen icon deletes the list with it.
- **Back up** from Settings now and then. Save the file to Files, or send it to yourself. A yellow dot on the Settings button means it has been over 30 days since the last backup.
- **Don't change the web address later.** iPhone ties the saved list to the address. If you do move it, back up first, then restore on the new address.

## Changing the app later

Edit `index.html`, then in `sw.js` change `basket-v1` to `basket-v2` (and so on) and upload both files again. The phone picks up the update the next time it opens the app with signal. It may need closing and reopening once.
