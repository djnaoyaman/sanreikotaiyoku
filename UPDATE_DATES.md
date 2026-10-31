# Page update dates

The visible **ページ更新** date describes the web page, including its presentation and referenced assets. It is not a medical review, a new research verification, a publication date or a claim of new evidence.

`page-updates.json` is the single source for the visible date, WebPage/ProfilePage `dateModified`, and the existing sitemap routes' `lastmod`. Initial dates reflect the verified 2026-10-30 20:05:37 UTC maison update (2026-10-31 05:05:37 JST). Existing research-check dates and `dateCreated` remain unchanged.

After a real change, explicitly stamp affected pages:

    python scripts/update_page_dates.py --date 2026-10-31T13:00:00+09:00 --paths index.html

For a change affecting all pages (only when true), use `--all`. A date and its timezone must be explicitly supplied; there is no build-time `today` fallback. Page hashes exclude their update labels but include referenced CSS, scripts, images and font dependencies. Changes require a deliberate date update and matching sitemap. Unchanged redeploys never advance dates. New or removed routes must update the ledger.

    python -m unittest discover -s tests -v
    python scripts/update_page_dates.py --check

The optional `--baseline-tree` flag is only for initial source-export preparation when binary assets are not locally copied. Production CI checks real checkout files and does not use that fallback. It must not be used to claim full local asset verification.

Do not overwrite historical `datePublished`, `dateCreated`, profile verification dates, research-review dates, citations or experimental dates. Date changes are reviewed independently from medical content.
