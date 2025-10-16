# 🌐 NGO Web Scraper: Configuration-Driven Data Extraction for Consistent Analytics

## Overview: The Data Quality Imperative

The **NGO Web Scraper** is a specialized, high-integrity data collection tool designed to extract essential organizational details from Non-Governmental Organization (NGO) websites and deliver a consistently structured Excel output. This project is built on the philosophy of **Configuration-Driven Design**, meaning the scraping logic is stable, and adapting to new sites or fixing broken selectors only requires updating the simple, declarative **YAML** configuration file.

### Key Data Points Collected

The scraper focuses on collecting normalized, actionable contact and profile information for clear analytics:

  * **NGO Name:** Retrieved robustly, primarily from the Open Graph meta tag `og:site_name`, with intelligent fallbacks to the page title or the primary `<h1>` heading.
  * **Address:** A precisely extracted office location using custom regular expressions applied to the contact pages.
  * **Contact Number:** One or more validated phone numbers, extracted using specialized rules that can prioritize preferred numbers (e.g., toll-free lines).
  * **Contact Person:** The name of a specific contact, optionally including their role or direct phone extension, often sourced from dedicated Media or Contact pages.
  * **Services Offered:** A **normalized, controlled list** of services (e.g., "Education", "Healthcare") ensuring consistency across different organizations for clean analytical reporting.
  * **Website & Source Pages:** Full domain and a record of all specific pages used for the data extraction process.

-----

## 🛠️ Project Structure and Setup

The project maintains a minimal and organized file structure:

  * `NGO_Web_Scraper.py`: The main Python script that handles loading YAML, scraping all domains, and writing the final Excel file.
  * `ngos.yaml`: The core configuration file where all NGO websites, target URLs (`contact_pages`), and precise extraction rules (regex, static values) are defined per domain.
  * `requirements.tx`: Lists all necessary Python packages and their specific versions, including `pandas`, `requests`, `beautifulsoup4`, and `PyYAML`, for environment setup.
  * `out/`: An output directory automatically created to store timestamped Excel reports, preventing collisions and preserving history.

### Setup and Execution

1.  **Environment:** Python 3.10+ is recommended.
2.  **Dependencies:** Install all required libraries using the provided requirements file:
    ```bash
    pip install -r requirements.tx
    ```
    (Key packages include `pandas`, `requests`, `beautifulsoup4`, `lxml`, and `PyYAML`).
3.  **Run:** Place `NGO_Web_Scraper.py` and `ngos.yaml` in the same folder, then execute the main script from the terminal.
      * **Default Run:** `python NGO_Web_Scraper.py`
      * **Custom Config Path:** `python NGO_Web_Scraper.py path\to\custom_config.yaml`

The console provides concise progress messages, showing configuration path, per-domain progress, validation summary, the Excel file path, and the final row count. The output file is saved to the `out/` directory with a timestamped filename like `ngo_contacts_YYYYMMDD_HHMMSS.xlsx`.

-----

## 💡 Design Philosophy: Robustness and Data Integrity

The scraper's architecture is built around flexibility and absolute data quality.

### Fail-Fast Validation (The "No Placeholders" Guarantee)

A critical design choice is the use of the `require()` function. If any field marked as required in the YAML configuration is not successfully extracted, the entire pipeline **fails fast** by raising an exception, rather than writing incomplete rows.

  * **Benefit:** This approach guarantees **no placeholders** (e.g., "N/A" or empty cells) in the final Excel output.
  * **Actionable Feedback:** The failure provides a clear error showing which domain and field is missing, allowing the user to refine the YAML selector *before* producing an incomplete dataset.

### Extraction Mechanics

The scraping process is highly efficient and adaptive:

1.  **Concurrent Fetching:** All declared `contact_pages` for a single NGO are fetched once (using connection reuse via the `Fetcher` class), and their HTML content is merged into a single text block for extraction.
2.  **Flexible Selectors:** The core functions (`apply_regex` and `extract_phones`) use powerful regular expressions (`regex_any`) to adapt to different website structures, ensuring a single engine can process diverse HTML layouts.
3.  **Phone Prioritization:** Phone numbers are found by generic or exact patterns, de-duplicated, and *prioritized* based on the `prefer` rule (e.g., to list a toll-free number first).
4.  **Name Retrieval:** The `og_site_name` function robustly looks for the Open Graph meta tag, falling back to the page title or the main `<h1>` if necessary.

-----

## 🚀 Adding a New NGO (The 2–5 Minute Workflow)

The configuration-driven design allows new sites to be onboarded rapidly without modifying any Python code. Use the existing `ngos.yaml` blocks as templates:

1.  **Find Pages:** Copy the website’s “Contact” page URL(s) into `contact_pages`; optionally add a page with a named contact (like Media) if needed.
2.  **Set Rules:** Define precise extraction rules tailored to the new site's HTML under the `selectors` block:
      * **`address.regex_any`:** Provide a regex pattern that uniquely picks the office address, including the city and pincode.
      * **`phones.regex_any` or `phones.prefer`:** Define patterns for phone numbers and set `required_min`.
      * **`services.static`:** Use a normalized, controlled list of labels (e.g., “Education”, “Healthcare”) for clean analysis.
      * **`contact_person`:** Define a `static` value or a `regex` (and optional `page`) that captures a Name and optional Phone from the text.
      * **`og_name.url`:** Specify the best page for finding the organization's name.
3.  **Test and Commit:** Re-run the script. If it fails due to a missing field, refine the specific regex in the YAML and re-run until the final Excel file is successfully generated. Commit only the updated `ngos.yaml` file.

-----

## 🔒 Security and Ethics

The project is designed to be ethical and respectful:

  * The script respects websites’ terms and rate limits by fetching only a small number of pages per site. It is intended only for public, non-login content.
  * It avoids collecting personal data beyond what organizations publicly publish for contact purposes.
