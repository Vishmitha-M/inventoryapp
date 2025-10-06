from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    product_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<Product {self.product_id} {self.name}>"

class Location(db.Model):
    location_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<Location {self.location_id} {self.name}>"

class ProductMovement(db.Model):
    movement_id = db.Column(db.String, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_location = db.Column(db.String, db.ForeignKey('location.location_id'), nullable=True)
    to_location = db.Column(db.String, db.ForeignKey('location.location_id'), nullable=True)
    product_id = db.Column(db.String, db.ForeignKey('product.product_id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product', backref='movements')
    from_loc = db.relationship('Location', foreign_keys=[from_location])
    to_loc = db.relationship('Location', foreign_keys=[to_location])

    def __repr__(self):
        return f"<Move {self.movement_id} {self.product_id} {self.qty}>")


@app.before_first_request
def create_tables():
    db.create_all()

# Home -> redirect to report
@app.route('/')
def home():
    return redirect(url_for('report'))

# Products CRUD
@app.route('/products')
def products():
    prods = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=prods)

@app.route('/products/add', methods=['GET','POST'])
def add_product():
    if request.method == 'POST':
        pid = request.form['product_id'].strip()
        name = request.form['name'].strip()
        if not pid or not name:
            flash('Both fields are required','danger')
            return redirect(url_for('add_product'))
        if Product.query.get(pid):
            flash('Product ID already exists','warning')
            return redirect(url_for('add_product'))
        p = Product(product_id=pid, name=name)
        db.session.add(p)
        db.session.commit()
        flash('Product added','success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Add', product=None)

@app.route('/products/edit/<pid>', methods=['GET','POST'])
def edit_product(pid):
    p = Product.query.get_or_404(pid)
    if request.method == 'POST':
        p.name = request.form['name'].strip()
        db.session.commit()
        flash('Product updated','success')
        return redirect(url_for('products'))
    return render_template('product_form.html', action='Edit', product=p)

@app.route('/products/delete/<pid>', methods=['POST'])
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted','info')
    return redirect(url_for('products'))

# Locations CRUD
@app.route('/locations')
def locations():
    locs = Location.query.order_by(Location.name).all()
    return render_template('locations.html', locations=locs)

@app.route('/locations/add', methods=['GET','POST'])
def add_location():
    if request.method == 'POST':
        lid = request.form['location_id'].strip()
        name = request.form['name'].strip()
        if not lid or not name:
            flash('Both fields are required','danger')
            return redirect(url_for('add_location'))
        if Location.query.get(lid):
            flash('Location ID already exists','warning')
            return redirect(url_for('add_location'))
        l = Location(location_id=lid, name=name)
        db.session.add(l)
        db.session.commit()
        flash('Location added','success')
        return redirect(url_for('locations'))
    return render_template('location_form.html', action='Add', location=None)

@app.route('/locations/edit/<lid>', methods=['GET','POST'])
def edit_location(lid):
    l = Location.query.get_or_404(lid)
    if request.method == 'POST':
        l.name = request.form['name'].strip()
        db.session.commit()
        flash('Location updated','success')
        return redirect(url_for('locations'))
    return render_template('location_form.html', action='Edit', location=l)

@app.route('/locations/delete/<lid>', methods=['POST'])
def delete_location(lid):
    l = Location.query.get_or_404(lid)
    db.session.delete(l)
    db.session.commit()
    flash('Location deleted','info')
    return redirect(url_for('locations'))

# Movements
@app.route('/movements')
def movements():
    moves = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()
    return render_template('movements.html', movements=moves, products=products, locations=locations)

@app.route('/movements/add', methods=['GET','POST'])
def add_movement():
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()
    if request.method == 'POST':
        mid = request.form['movement_id'].strip()
        pid = request.form['product_id']
        from_loc = request.form.get('from_location') or None
        to_loc = request.form.get('to_location') or None
        qty = int(request.form['qty'] or 0)
        if not mid or not pid or qty<=0:
            flash('Please provide movement id, product and positive qty','danger')
            return redirect(url_for('add_movement'))
        if ProductMovement.query.get(mid):
            flash('Movement ID exists','warning')
            return redirect(url_for('add_movement'))
        move = ProductMovement(movement_id=mid, product_id=pid, from_location=from_loc, to_location=to_loc, qty=qty)
        db.session.add(move)
        db.session.commit()
        flash('Movement recorded','success')
        return redirect(url_for('movements'))
    return render_template('movement_form.html', products=products, locations=locations, action='Add', movement=None)

# Report: balance per (product, location)
@app.route('/report')
def report():
    # compute balances
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()
    # initialize balance dict
    balance = {}
    for p in products:
        for l in locations:
            balance[(p.product_id, l.location_id)] = 0

    moves = ProductMovement.query.all()
    for m in moves:
        # incoming to to_location
        if m.to_location:
            key = (m.product_id, m.to_location)
            balance[key] = balance.get(key, 0) + m.qty
        # outgoing from from_location
        if m.from_location:
            key = (m.product_id, m.from_location)
            balance[key] = balance.get(key, 0) - m.qty

    # prepare rows for grid view (only non-zero or show zeros depending)
    rows = []
    for (pid, lid), qty in balance.items():
        if qty != 0:
            prod = Product.query.get(pid)
            loc = Location.query.get(lid)
            rows.append({'product': prod.name, 'product_id': pid, 'location': loc.name, 'location_id': lid, 'qty': qty})
    # sort rows
    rows = sorted(rows, key=lambda r: (r['product'], r['location']))

    return render_template('report.html', rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
