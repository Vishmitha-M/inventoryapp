# Flask Inventory Management (Beginner level)

This is a simple inventory management web application built with Flask and SQLite.
It supports:
- Add / Edit / View Products
- Add / Edit / View Locations (warehouses)
- Record Product Movements (from / to locations, qty)
- Balance report showing product quantities per location

## How to run (locally)
1. Create a virtualenv (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python app.py
   ```
3. Open http://127.0.0.1:5000/ in your browser.

## Notes for the hiring test
- Uses SQLite for simplicity. Primary keys are text (product_id, location_id, movement_id).
- Movements allow either `from_location` or `to_location` (or both). If `from_location` is blank, it is considered incoming; if `to_location` is blank, it is outgoing.
- The report computes balances by aggregating movements: incoming adds qty, outgoing subtracts qty.
- Designed to be beginner-friendly with Bootstrap UI.

## Files
- app.py : main Flask app
- templates/ : HTML templates using Bootstrap 5
- static/style.css : small custom styles
- requirements.txt : packages list

## Tips
- Create 3-4 products and locations and make ~20 movements to test balances.
- Use Movement IDs like M001, M002... Product IDs like P001, P002. Location IDs like L001, L002.

