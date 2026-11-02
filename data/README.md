# Dataset attribution and provenance

**SMS Spam Collection**, Almeida, T. & Hidalgo, J. (2011). UCI Machine Learning Repository. DOI: https://doi.org/10.24432/C5CC84

- Source page: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
- Download: https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip
- License listed by UCI: **Creative Commons Attribution 4.0 International** (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
- `raw/SMSSpamCollection` contains the unmodified labelled corpus. SHA-256: `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d`.
- `raw/original-readme.txt` is the original source readme, retained unmodified in its original Latin-1 encoding. It describes contributing corpora and research history.
- Downloaded during the November 2026 upgrade. 5,574 labelled records were parsed from the downloaded file.

The training pipeline removes case/whitespace duplicates, groups normalised templates, splits records, and derives TF-IDF and logistic regression parameters. These transformations and the results are documented in `docs/MODEL_CARD.md`; raw source text is unchanged. Preserve this attribution and license link when redistributing the data or derived model. The repository's code MIT license does not replace the dataset's separate license.

The corpus contains historical user-submitted SMS, including phone-like strings and URLs. The app does not expose raw corpus examples in its interface or contact/visit anything in the corpus. Its demonstration conversations are separately authored fictional examples in `examples.py`.
