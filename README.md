# 🏦 UBA Branch Finder (Python)

This project provides a **Python implementation** to search and fuzzy-match the locations of **UBA bank branches in Nigeria**.  

The script uses a **CSV dataset** of UBA branches, integrates fuzzy matching (`rapidfuzz`) for flexible searches, and performs geocoding using **OpenStreetMap’s Nominatim API** (Nigeria only). It also includes a Streamlit application for interactive usage.

---

## Files

* **Python Implementation**
  * `app.py`: Streamlit application for branch search and fuzzy matching.
  * `uba_branches_notebook.ipynb`: Jupyter notebook version for testing outside Streamlit.
* **Dataset**
  * `uba_branches.csv`: CSV file containing the list of UBA branches and their addresses.
* **Documentation**
  * `README.md`: This file.

---

## Prerequisites

### 🔹 For Python

* Python 3.8+ installed.
* Required packages:

  * `pandas`
  * `requests`
  * `rapidfuzz`
  * `streamlit`

Install with:

```bash
pip install -r requirements.txt
