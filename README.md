# Tanish Urbania

Landing site and guides for **Tanish Urbania, Charholi, PCMC, Pune** (Tanish Group). Live: https://tanish-urbania.com

Plain static HTML, CSS and vanilla JS. No build step.

## Structure
- `index.html` landing page; `blog/` guides (overview, location, investment, schools, hospitals, IT hubs, malls, buying guides) and `blog/project/` project pages
- `sitemap/` HTML site map, `sitemap.xml`, `robots.txt`, `.htaccess`
- `css/style.css`, `config.js` (project, developer, manager, Supabase), `form.js`, `index.js`, `fonts/` (self-hosted), `images/`

## Notes
- Update the `?v=` tag on CSS and JS links whenever those files change (cache-busting).
- Every content image needs alt text that includes "Tanish Urbania".
- `scripts/improve.py` is the one-off upgrade script used to fix images and icons, add the project pages, fonts, schema, site map and `.htaccess`. It is kept for reference and is not served.

## Deploy
Hostinger static hosting for tanish-urbania.com. Upload the site files (without `.git`, `scripts/`, `*.md`) or connect the GitHub repo in hPanel for auto-deploy.
