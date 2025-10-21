# import re
# import requests
# from datetime import datetime
# from Config import Session
# from Model import Books
# from bs4 import BeautifulSoup
#
# REQUEST_TIMEOUT = 20
#
# # -------- Google Books Metadata Fetcher --------
# def fetch_google_books(query, max_results=10):
#     """
#     Fetch metadata (title, author, description, cover, category)
#     from Google Books API.
#     """
#     url = "https://www.googleapis.com/books/v1/volumes"
#     params = {"q": query, "maxResults": max_results}
#     response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
#     data = response.json()
#
#     books = []
#     for item in data.get("items", []):
#         info = item.get("volumeInfo", {})
#         books.append({
#             "title": info.get("title"),
#             "author": ", ".join(info.get("authors", [])) if info.get("authors") else "Unknown",
#             "description": info.get("description", ""),
#             "cover_image_url": info.get("imageLinks", {}).get("thumbnail", ""),
#             "category": info.get("categories", ["Uncategorized"])[0],
#         })
#     return books
#
#
# # -------- Import Into Database + Fulltext Enrichment --------
# def import_books_with_optional_fulltext(google_books: list, also_fulltext: bool = False):
#     """
#     Insert Google metadata; optionally enrich each row with full text
#     from Gutenberg / Open Library.
#     """
#     from Controller import get_public_domain_fulltext  # local import to avoid circular dependency
#
#     session = Session()
#     inserted_ids = []
#     enriched_count = 0
#     try:
#         for gb in google_books:
#             book = Books(
#                 title=gb["title"],
#                 author=gb["author"],
#                 description=gb["description"],   # replaced if fulltext available
#                 cover_image_url=gb["cover_image_url"],
#                 category=gb["category"],
#                 created_at=datetime.utcnow()
#             )
#             session.add(book)
#             session.flush()  # get book_id
#             inserted_ids.append(book.book_id)
#
#             if also_fulltext:
#                 fulltext, _src = get_public_domain_fulltext(gb["title"], gb["author"])
#                 if fulltext:
#                     book.description = fulltext
#                     enriched_count += 1
#
#         session.commit()
#         return {"inserted": len(inserted_ids), "enriched": enriched_count}
#     except Exception as e:
#         session.rollback()
#         raise e
#     finally:
#         session.close()
#
#
# # -------- Fulltext Helpers --------
# def _clean_gutenberg(text: str) -> str:
#     """Strip Project Gutenberg boilerplate headers/footers."""
#     if not text:
#         return text
#     start_pat = r"\*\*\*\s*START OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*"
#     end_pat   = r"\*\*\*\s*END OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*"
#     text = re.split(start_pat, text, flags=re.IGNORECASE | re.DOTALL)[-1]
#     text = re.split(end_pat,   text, flags=re.IGNORECASE | re.DOTALL)[0]
#     return text.strip()
#
# def _normalize_ws(text: str) -> str:
#     """Normalize whitespace for cleaner text."""
#     return re.sub(r"[ \t]+\n", "\n", text).replace("\r\n", "\n").strip() if text else text
#
# def _strip_html(raw_html: str) -> str:
#     """Convert HTML to plain text (fallback when only .html is available)."""
#     return BeautifulSoup(raw_html, "html.parser").get_text(" ", strip=True)
#
# def _ia_pick_text_url(ia_id: str):
#     """Pick the best plain text file from Internet Archive metadata."""
#     meta_url = f"https://archive.org/metadata/{ia_id}"
#     m = requests.get(meta_url, timeout=REQUEST_TIMEOUT)
#     if m.status_code != 200:
#         return None
#
#     files = m.json().get("files", [])
#     for f in files:
#         name = (f.get("name") or "").lower()
#         if name.endswith(".txt"):
#             return f"https://archive.org/download/{ia_id}/{f['name']}"
#     return None
#
#
# # -------- Fulltext Fetchers --------
# def fetch_openlibrary_fulltext(title: str, author: str = ""):
#     """Try to fetch full text from Open Library / Internet Archive."""
#     try:
#         q = f"{title} {author}".strip().replace(" ", "+")
#         url = f"https://openlibrary.org/search.json?q={q}"
#         r = requests.get(url, timeout=REQUEST_TIMEOUT)
#         r.raise_for_status()
#         docs = r.json().get("docs", [])
#         for d in docs:
#             if d.get("has_fulltext") and d.get("ebook_access") == "public":
#                 ia_list = d.get("ia") or []
#                 for ia_id in ia_list:
#                     txt_url = _ia_pick_text_url(ia_id)
#                     if not txt_url:
#                         continue
#                     t = requests.get(txt_url, timeout=REQUEST_TIMEOUT)
#                     if t.status_code == 200 and len(t.text.strip()) > 1000:
#                         raw_text = t.text
#                         if raw_text.lstrip().startswith("<html") or "<html" in raw_text.lower():
#                             raw_text = _strip_html(raw_text)
#                         return _normalize_ws(raw_text)
#     except Exception:
#         pass
#     return None
#
#
# def fetch_gutenberg_fulltext(title: str, author: str = ""):
#     """Use Gutendex to find a PD book and download the plain text."""
#     try:
#         q = "+".join([p for p in [title, author] if p]).strip()
#         url = f"https://gutendex.com/books?search={q}"
#         r = requests.get(url, timeout=REQUEST_TIMEOUT)
#         r.raise_for_status()
#         results = r.json().get("results", [])
#         for b in results:
#             if b.get("copyright") is False and ("en" in b.get("languages", ["en"])):
#                 fmts = b.get("formats", {})
#                 txt = fmts.get("text/plain; charset=utf-8") or fmts.get("text/plain")
#                 if txt:
#                     t = requests.get(txt, timeout=REQUEST_TIMEOUT)
#                     if t.status_code == 200 and len(t.text.strip()) > 1000:
#                         raw_text = t.text
#                         if raw_text.lstrip().startswith("<html") or "<html" in raw_text.lower():
#                             raw_text = _strip_html(raw_text)
#                         return _normalize_ws(_clean_gutenberg(raw_text))
#     except Exception:
#         pass
#     return None
#
#
# # -------- Orchestrator --------
# def get_public_domain_fulltext(title: str, author: str = ""):
#
#     # 1. Project Gutenberg first
#     text = fetch_gutenberg_fulltext(title, author)
#     if text:
#         return text, "project_gutenberg"
#
#     # 2. If not found → try Open Library
#     text = fetch_openlibrary_fulltext(title, author)
#     if text:
#         return text, "openlibrary_internet_archive"
#
#     return None, None


