# The Rewrite Project

This is the website for Brian's free, non-commercial Buffy the Vampire Slayer Season Six and Seven Rewrite Project, a full-cast audio drama.

The pages are plain HTML and CSS. There is nothing to install and no build step. GitHub Pages publishes the `main` branch at <https://brianbelmont87.github.io>. After a change is on `main`, the live site updates on its own. It can take a minute. The video players need an internet connection.

To preview the layout on your computer, open `index.html` in a web browser.

## Folder layout

- `index.html` — home page
- `episodes.html` — every episode, each with its own player
- `about.html` — a short about note and the disclaimer
- `css/style.css` — colors, boxes, and layout. You do not need to edit this to add an episode.
- `images/banner_sunnydale_final.jpg` — the header banner on every page. Leave this file name as it is.
- `favicon.svg` — the small moon icon in the browser tab
- `fonts/` — the typefaces the site uses (Cinzel for headings, Atkinson Hyperlegible for the text you read). Leave this folder alone. The license files in there are required.
- `.nojekyll` — an empty file that tells GitHub Pages to publish these files as they are. Leave it in place.

The banner, the Navigate box, the side boxes, and the footer are copied onto each page. If you change a link in the Navigate box or the footer, make the same change in `index.html`, `episodes.html`, and `about.html`.

## How to add a new episode

You will copy one episode block, then change the title and the video id. Use a plain text editor (not a word processor).

1. Open `episodes.html`.
2. Find an episode block. It starts with `<article class="panel"` and ends with `</article>`. The Ep 08 block is a good one to copy.
3. Copy that whole block and paste the copy underneath the last episode.
4. In the copy, change these four things so they all use the new episode:
   - `id="ep-08"` becomes something new, such as `id="ep-15"`. This is the bookmark name. Use letters, numbers, and hyphens only, and do not reuse a name that is already on the page.
   - The title between `<span>` and `</span>`, for example `Ep 15 – Your Title`.
   - The same title inside `title="..."`.
   - The video id, which is the only part of the player address you should change.

   A player address looks like this:

   `https://www.youtube-nocookie.com/embed/J-URVlMdhOE`

   `J-URVlMdhOE` is the video id for Ep 08. Replace that id and leave `youtube-nocookie.com/embed/` as it is.

   On YouTube, the id is the short code in the video address: the part after `watch?v=` and before any `&`. If the address looks like `youtu.be/THIS_PART`, then `THIS_PART` is the id.

5. Open `index.html`. In the Episode Guide, copy one `<li>...</li>` line, paste it in episode order, and point it at the new bookmark. For the example above, the line would be:

   `<li><a href="episodes.html#ep-15">Ep 15 – Your Title</a></li>`

   The `#ep-15` part must match the `id` you chose in step 4.

6. If this new episode is the newest one, update the Latest Episode box on the home page (it is marked with a comment that says `LATEST EPISODE`). Change the title in the link and in `title="..."`, and replace the video id in the player address. Point the link at the new bookmark, such as `episodes.html#ep-15`.

7. Save both files. Commit them to the `main` branch (or merge a pull request into `main`).

You do not need to edit `about.html` or `css/style.css` when you add an episode.

## Changing the welcome and about text

On the home page, the welcome paragraph is marked with a comment that starts `WELCOME TEXT`. Replace that paragraph with your own words. Leave the comment there if you want a reminder, or delete the comment once you are done.

On the About page, the paragraph marked `ABOUT TEXT` is yours to replace. The Disclaimer paragraph under it is the project disclaimer. It also appears in the footer of every page. If you change that wording, change it in the footer of all three pages as well.
