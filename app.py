from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import threading
import asyncio
import websockets
import websocket_server

app = Flask(__name__) # framework in python that permits the creation of api

# Database configuration - using existing database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:alexandrina@localhost:5432/makeup_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)


# Product Model - maps to existing table
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    link = db.Column(db.String, nullable=False)
    year = db.Column(db.String)
    gama_de_produse = db.Column(db.String)
    volume = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 1. Create - POST for one product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        # Get data from request
        data = request.json

        # Create new product
        new_product = Product(
            title=data['title'],
            name=data['name'],
            price=data['price'],
            link=data['link'],
            year=data.get('year'),  # .get() for optional fields
            gama_de_produse=data.get('gama_de_produse'),
            volume=data.get('volume')
        )

        # Add to database
        db.session.add(new_product)
        db.session.commit()

        # Return the created product
        return jsonify({
            "message": "Product created successfully",
            "product": {
                "id": new_product.id,
                "title": new_product.title,
                "name": new_product.name,
                "price": new_product.price,
                "link": new_product.link,
                "year": new_product.year,
                "gama_de_produse": new_product.gama_de_produse,
                "volume": new_product.volume
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 2. Read - GET endpoints with pagination
@app.route('/products', methods=['GET'])
def get_products():
    try:
        # Get pagination parameters from query string
        offset = request.args.get('offset', default=0, type=int)
        limit = request.args.get('limit', default=5, type=int)

        # Query products with pagination
        products = Product.query.offset(offset).limit(limit).all()

        # Convert to list of dictionaries
        products_list = []
        for product in products:
            products_list.append({
                "id": product.id,
                "title": product.title,
                "name": product.name,
                "price": product.price,
                "link": product.link,
                "year": product.year,
                "gama_de_produse": product.gama_de_produse,
                "volume": product.volume,
                "created_at": product.created_at,
                "updated_at": product.updated_at
            })

        # Return list of products
        return jsonify({
            "products": products_list,
            "total": len(products_list),
            "offset": offset,
            "limit": limit
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Get single product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    try:
        product = Product.query.get(id)
        if product:
            return jsonify({
                "id": product.id,
                "title": product.title,
                "name": product.name,
                "price": product.price,
                "link": product.link,
                "year": product.year,
                "gama_de_produse": product.gama_de_produse,
                "volume": product.volume,
                "created_at": product.created_at,
                "updated_at": product.updated_at
            }), 200
        return jsonify({"message": "Product not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 3. Update - PUT endpoint
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    try:
        product = Product.query.get(id)
        if not product:
            return jsonify({"message": "Product not found"}), 404

        data = request.json

        # Update fields if they are in the request
        if 'title' in data:
            product.title = data['title']
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            product.price = data['price']
        if 'link' in data:
            product.link = data['link']
        if 'year' in data:
            product.year = data['year']
        if 'gama_de_produse' in data:
            product.gama_de_produse = data['gama_de_produse']
        if 'volume' in data:
            product.volume = data['volume']

        product.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": "Product updated successfully",
            "product": {
                "id": product.id,
                "title": product.title,
                "name": product.name,
                "price": product.price,
                "link": product.link,
                "year": product.year,
                "gama_de_produse": product.gama_de_produse,
                "volume": product.volume,
                "updated_at": product.updated_at
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 4. Delete - DELETE endpoint
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    try:
        product = Product.query.get(id)
        if not product:
            return jsonify({"message": "Product not found"}), 404

        db.session.delete(product)
        db.session.commit()

        return jsonify({
            "message": "Product deleted successfully",
            "id": id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 5. File Upload for multiple products
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        # Check if it's a JSON file
        if not file.filename.endswith('.json'):
            return jsonify({"error": "Only JSON files are allowed"}), 400

        # Read and parse JSON file
        data = json.load(file)

        # Handle both direct list and nested "filtered_products"
        products_data = data.get("filtered_products", data)
        if not isinstance(products_data, list):
            return jsonify({"error": "Invalid JSON format"}), 400

        # Count successfully added products
        added_count = 0

        # Add each product to database
        for product_data in products_data:
            try:
                new_product = Product(
                    title=product_data['title'],
                    name=product_data['name'],
                    price=product_data['price'],
                    link=product_data['link'],
                    year=product_data.get('year'),
                    gama_de_produse=product_data.get('gama_de_produse'),
                    volume=product_data.get('volume')
                )
                db.session.add(new_product)
                added_count += 1
            except Exception as e:
                print(f"Error adding product: {str(e)}")
                continue

        db.session.commit()

        return jsonify({
            "message": "File processed successfully",
            "products_added": added_count
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


def start_websocket_server():
    asyncio.run(websocket_server.start_server())



if __name__ == '__main__':
# Start WebSocket server in a separate thread
    ws_thread = threading.Thread(target=start_websocket_server)
   # ws_thread.daemon = True
    ws_thread.start()

    # Start Flask server
    app.run(debug=True, port=5000)