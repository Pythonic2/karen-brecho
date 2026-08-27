# Telles' Thrift Shop

A self-service thrift shop built with Django, HTMX, HTML and CSS. Store management is handled through Django Admin; the customer-facing experience is entirely in English.

## Local setup

```bash
uv venv
uv pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Open `http://127.0.0.1:8002/` for the kiosk and `/admin/` for management. Create suppliers, categories and products in Admin before testing a purchase.

## Development payment

Checkout displays a fake PIX screen. Clicking **Simulate approved payment** marks the sale and products as paid, records the customer/product/supplier relationship, and sends a receipt through Django's console email backend. The confirmation screen returns to the welcome page after 12 seconds.

## Consignment configuration

Campaign dates and percentages live in `telles_shop/settings.py`:

- `CONSIGNMENT_PERIOD_START`
- `CONSIGNMENT_HIGH_RATE_DEADLINE`
- `CONSIGNMENT_PERIOD_END`
- `CONSIGNMENT_HIGH_RATE`
- `CONSIGNMENT_STANDARD_RATE`
- `LANGUAGE_CENTER_RATE`
- `OWNER_RATE`

Opening campaign pieces received and sold from September 7 through September 11 earn the supplier 50%. All later pieces and sales earn 30%. After the supplier share, the remainder is divided 30% to Mariane Telles Language Center and 70% to the owner.

Run checks with:

```bash
.venv/bin/python manage.py test
.venv/bin/python manage.py check
```

## Docker deployment

Production settings are centralized in Portainer's stack environment variables. Use “Load variables from .env file” to import the root `.env`; Portainer stores those values in the stack rather than creating a physical `.env` file. Compose passes the imported variables to Django without duplicating their values in YAML. The current base URL is `https://telles-thrift-shop.gestcloud.com.br`.

```bash
docker compose up -d --build
docker compose exec app python manage.py createsuperuser
```

The application uses port `8002` internally and externally (`8002:8002`) and joins the existing external Docker network `pi_default`. SQLite, uploaded media and collected static files use named volumes; the application code remains safely inside the built image. Configure the existing HTTPS reverse proxy to forward `telles-thrift-shop.gestcloud.com.br` to `telles-thrift-shop:8002` through `pi_default`, or to `127.0.0.1:8002` from the host.

To load the optional demonstration catalog:

```bash
docker compose exec app python manage.py seed_demo
```

The development email backend prints messages in `docker compose logs app`. Configure the SMTP variables in `.env` to send real email.
