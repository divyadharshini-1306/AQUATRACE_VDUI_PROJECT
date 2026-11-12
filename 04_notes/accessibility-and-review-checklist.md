# AquaTrace Accessibility and Peer-Review Checklist

Each person reviews one other person's pages with this list. Mark each item Pass, Fail or N/A, and add a note for every Fail.

Reviewer: ____  Pages reviewed: ____  Date: ____

## A. Core review checklist (shared by everyone)

| # | Check | Pass / Fail / N/A | Notes |
| --- | --- | --- | --- |
| 1 | Every visual has a clear title. Ideally the title states the finding (an insight sentence). | | |
| 2 | Axes are labelled, with units where they matter (for example litres per kWh, share of facility-years %). | | |
| 3 | No chart junk: no 3D effects, heavy gridlines, unnecessary borders or decoration. | | |
| 4 | Colours are accessible: the shared theme palette is used and Low, Medium and High are distinguishable. | | |

## B. Accessibility checks (owner: Member 4)

| # | Check | Pass / Fail / N/A | Notes |
| --- | --- | --- | --- |
| 5 | Shared theme (aquatrace-theme.json) is applied. | | |
| 6 | Every visual, card, table and slicer has alt text that says what it shows and why it matters. | | |
| 7 | Tab order follows reading order: headline numbers, then charts, then slicers. | | |
| 8 | Text contrast is at least 4.5:1 against its background (check with webaim.org/resources/contrastchecker). | | |
| 9 | Meaning is not carried by colour alone. Data labels, legends or text back it up. | | |
| 10 | Data labels are readable on every bar colour (white on blue, black on orange and vermillion). | | |
| 11 | Terms like WUE and PUE are explained in a subtitle or note. | | |
| 12 | Subtitles say "modelled estimates" where relevant. | | |
| 13 | Slicers are labelled in plain words (no underscores) and fully visible, with no cut-off options. | | |
| 14 | Navigation buttons are in the same position on every page and have alt text. | | |
| 15 | At most five main visuals per page. | | |
| 16 | Colour-blind check done (for example Colour Oracle: deuteranopia, protanopia, tritanopia). | | |

## C. Page 1 status (self-check, 12 November 2026)

| Item | Status |
| --- | --- |
| Theme applied (imported in Desktop by a teammate) | Done |
| Risk chart recoloured to blue, orange and vermillion | Done |
| Risk chart data labels readable, counts removed | Done |
| Facility Count card shows 1200 instead of 1.200K | Done |
| Slicer heading renamed to "Cooling system" | Done |
| Alt text on all visuals and slicers | Done |
| Tab order set (cards, table, charts, slicers) | Done |
| Summary table has a title | Done |
| Axis title wording consistent ("Cooling system" vs "Cooling System") | Open |
| Region slicer shows all options (North America is cut off) | Open, needs Member 1 |
| Colour-blind simulation test | Open |
| Alt text numbers checked against final data | Open |
| Page title and navigation buttons | Open, waiting for other pages |

## D. How to run a review in 10 minutes

1. Open the other person's pages in Reading view.
2. Go through the table above and mark each row.
3. Write the Fails in the group chat with a screenshot and the page name.
4. The page owner fixes them and replies "done".
5. Recheck only the Fails.
