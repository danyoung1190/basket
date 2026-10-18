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
- **New shop or list**: tap **+ Add** at the end of the tabs.
- **Send to a shop**: hold an item, then tap a shop. "Send N to their usual shops" sorts everything she has sent somewhere before.
- **Reorder**: drag the handle on the right of an item. Drag it under a section heading, such as Fridge, to file it there.
- **Tick off**: tap an item. Ticked items go grey at the bottom. Tap **Clear** when she has finished shopping.
- **Shop settings** (the ... button, or hold a shop's tab): rename it, change its colour, show its sharing code if it's shared, and add sections in the order she walks round the shop. Supermarkets start with standard sections; other shops start with none.
- **Share**: the share button sends the list as text, for example to WhatsApp.
- **Undo**: every move, removal or clear shows an Undo button for 6 seconds.
- **Recently removed**: open Settings to restore anything that was removed or cleared.

## Sharing a list between phones

A shared list is an extra tab (for example "Home") that every phone on it can see and edit, live. Your own shops stay private. Nobody needs an account.

- **Create:** tap **+ Add** > **New shared list**, name it. It shows a QR code and a code like `BSKT-7K2M-Q9RD-4XNP-W8TA`. To show it again later: open the list, tap **•••** > **Share code**.
- **Join, in the same room:** on the other phone open Basket, tap **+ Add** > **Join a shared list** > **Scan their code**, and point it at the QR. Scan from inside Basket, not with the Camera app: iPhone opens Camera links in Safari, which can't reach the Home Screen app.
- **Join, from a message:** the **Send** button writes a message with the code. They copy the whole message, then in Basket tap **+ Add** > **Join a shared list** > **Paste a code**. Basket finds the code in the message.

Behind the scenes the lists live in a free Google Firebase project that you set up once. Family use stays well inside the free limits.

**One-off setup (about 15 minutes, on the computer):**
1. Go to console.firebase.google.com, sign in with a Google account, and click **Create a project**. Name it `basket`. Turn Google Analytics off. Create.
2. Left menu **Build > Authentication** > **Get started** > **Anonymous** > turn **Enable** on > Save.
3. **Build > Firestore Database** > **Create database** > pick a European location (for example europe-west2, London) > **Start in production mode** > Create.
4. In Firestore open the **Rules** tab, replace everything with the rules below, and click **Publish**.
5. Click the gear next to **Project Overview** > **Project settings**. Scroll to **Your apps**, click the **</>** (web) icon, nickname `Basket`, leave Hosting unticked, **Register app**. It shows a block starting `const firebaseConfig = {`. Copy the lines between the braces.
6. Open `firebase-config.js` from this folder in a text editor and paste those lines between its braces, so it looks like:
   ```
   window.BASKET_FIREBASE = {
     apiKey: "AIza...",
     authDomain: "basket-xxxx.firebaseapp.com",
     projectId: "basket-xxxx",
     storageBucket: "basket-xxxx.appspot.com",
     messagingSenderId: "1234567890",
     appId: "1:1234567890:web:abc123"
   };
   ```
   These values identify your project; they are not secret, so it is fine for them to be in a public repository.
7. Upload `firebase-config.js` to GitHub with the rest of the files. Done.

**Firestore rules** (step 4):
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /lists/{listId} {
      allow read, write: if request.auth != null;
      match /items/{itemId} {
        allow read, write: if request.auth != null;
      }
    }
  }
}
```
Lists are protected by their codes, which are random and long enough that they cannot be guessed. Only give a code to people you want on the list.

**Day to day:** changes appear on the other phones within a second or two while online. With no signal, changes queue and send later, and the tab says so. Pull the list down or tap the refresh arrows to check now. Anything the other person removes lands in your Recently removed. Leaving a list (the ... button > Leave shared list) only removes it from your phone.

## Important things to know

- **Private lists live only on the phone.** Deleting the Home Screen icon deletes them with it. Shared lists come back when you re-enter their codes.
- **Back up** from Settings now and then. Save the file to Files, or send it to yourself. A yellow dot on the Settings button means it has been over 30 days since the last backup.
- **Don't change the web address later.** iPhone ties the saved list to the address. If you do move it, back up first, then restore on the new address.

## Changing the app later

Edit `index.html`, then in `sw.js` change `basket-v1` to `basket-v2` (and so on) and upload both files again. The phone picks up the update the next time it opens the app with signal. It may need closing and reopening once.
