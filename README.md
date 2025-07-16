OpticOasis — E-commerce Eyewear Web App

Welcome to OpticOasis, a modern e-commerce platform built to offer a smooth and stylish shopping experience for premium eyewear.
Developed using Django MVT architecture with server-rendered HTML templates.

Live on : https://opticoasis.life/

🚀 Features
🛍️ User Features
Product Browsing & Search — Explore a wide range of eyewear products.

Product Details — View product descriptions, images, and specifications.

Cart Management — Add, update, and remove items easily.

Wishlist — Save favorite products for future purchase.

Order Placement — Smooth checkout and order process.

Profile Management — Update personal information and view order history.

Google Sign-In — Sign up and login quickly using your Google account.

👨‍💼 Admin Features
Product Management — Add, edit, or remove products and manage inventory.

Order Management — View and update order statuses.

Coupon Management — Create and manage discount coupons.

Return & Refund — Handle return requests and process refunds.

💻 Tech Stack
Backend: Django (MVT architecture)

Database: PostgreSQL or MySQL (configurable)

Frontend: Django templates, HTML, CSS, Bootstrap

Authentication: Django auth system with Google OAuth integration

Deployment: Nginx + Gunicorn (recommended)

⚙️ Setup Instructions
1️⃣ Clone the repository
bash
Copy
Edit
git clone https://github.com/AswinNarayananT/OpticOasis-ecommerse-webapp.git
cd OpticOasis-ecommerse-webapp
2️⃣ Create and activate virtual environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3️⃣ Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
4️⃣ Configure environment variables
Create a .env file in the project root (or configure directly in settings.py).

Example keys:

env
Copy
Edit
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=your_database_url
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_password
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
5️⃣ Run migrations
bash
Copy
Edit
python manage.py migrate
6️⃣ Create a superuser
bash
Copy
Edit
python manage.py createsuperuser
7️⃣ Collect static files
bash
Copy
Edit
python manage.py collectstatic
8️⃣ Start the development server
bash
Copy
Edit
python manage.py runserver
Visit: http://localhost:8000/

🛡️ Deployment
Recommended stack: Nginx + Gunicorn

Example (Gunicorn):

bash
Copy
Edit

gunicorn backend.wsgi:application --bind 0.0.0.0:8000
📄 Features Summary
Module	Features
User	Profile, Wishlist, Cart, Order Placement, Google Sign-In
Admin	Products, Orders, Coupons, Returns & Refunds

💬 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

📄 License
This project is licensed under the MIT License.

🙌 Acknowledgements
Django community & documentation

Google OAuth

Bootstrap

✉️ Contact
Aswin Narayanan T

📧 [aswinmalamakkavu@gmail.com]

🌐 [www.linkedin.com/in/aswin-nt]