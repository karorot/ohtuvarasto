from flask import Flask, render_template, request, redirect, url_for, flash
from varasto import Varasto


class WarehouseManager:
    def __init__(self):
        self.varastot = {}
        self.next_id = 1

    def get_all(self):
        return self.varastot

    def get(self, varasto_id):
        return self.varastot.get(varasto_id)

    def create(self, nimi, tilavuus, alku_saldo=0.0):
        if not nimi or tilavuus <= 0:
            return None
        varasto_id = self.next_id
        self.next_id += 1
        self.varastot[varasto_id] = {
            "nimi": nimi,
            "varasto": Varasto(tilavuus, alku_saldo)
        }
        return varasto_id

    def update(self, varasto_id, nimi, tilavuus):
        if varasto_id not in self.varastot or not nimi or tilavuus <= 0:
            return False
        old_saldo = self.varastot[varasto_id]["varasto"].saldo
        self.varastot[varasto_id] = {
            "nimi": nimi,
            "varasto": Varasto(tilavuus, min(old_saldo, tilavuus))
        }
        return True

    def delete(self, varasto_id):
        if varasto_id in self.varastot:
            del self.varastot[varasto_id]
            return True
        return False

    def reset(self):
        self.varastot = {}
        self.next_id = 1


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_manager(app):
    if not hasattr(app, 'warehouse_manager'):
        app.warehouse_manager = WarehouseManager()
    return app.warehouse_manager


def register_index_route(app):
    @app.route("/")
    def index():
        mgr = get_manager(app)
        return render_template("index.html", varastot=mgr.get_all())


def register_create_route(app):
    @app.route("/create", methods=["GET", "POST"])
    def create():
        if request.method == "POST":
            return handle_create_post(app)
        return render_template("create.html")


def handle_create_post(app):
    mgr = get_manager(app)
    nimi = request.form.get("nimi", "").strip()
    tilavuus = parse_float(request.form.get("tilavuus", 0))
    alku_saldo = parse_float(request.form.get("alku_saldo", 0))
    result = mgr.create(nimi, tilavuus, alku_saldo)
    if result is None:
        flash("Virhe: Anna kelvollinen nimi ja kapasiteetti.", "error")
        return render_template("create.html")
    return redirect(url_for("index"))


def register_view_route(app):
    @app.route("/warehouse/<int:varasto_id>")
    def warehouse(varasto_id):
        mgr = get_manager(app)
        data = mgr.get(varasto_id)
        if not data:
            return redirect(url_for("index"))
        return render_template(
            "warehouse.html", varasto_id=varasto_id, data=data
        )


def register_add_route(app):
    @app.route("/warehouse/<int:varasto_id>/add", methods=["POST"])
    def add_products(varasto_id):
        mgr = get_manager(app)
        data = mgr.get(varasto_id)
        if data:
            maara = parse_float(request.form.get("maara", 0))
            data["varasto"].lisaa_varastoon(maara)
        return redirect(url_for("warehouse", varasto_id=varasto_id))


def register_remove_route(app):
    @app.route("/warehouse/<int:varasto_id>/remove", methods=["POST"])
    def remove_products(varasto_id):
        mgr = get_manager(app)
        data = mgr.get(varasto_id)
        if data:
            maara = parse_float(request.form.get("maara", 0))
            data["varasto"].ota_varastosta(maara)
        return redirect(url_for("warehouse", varasto_id=varasto_id))


def register_edit_route(app):
    @app.route("/warehouse/<int:varasto_id>/edit", methods=["GET", "POST"])
    def edit_warehouse(varasto_id):
        mgr = get_manager(app)
        data = mgr.get(varasto_id)
        if not data:
            return redirect(url_for("index"))
        if request.method == "POST":
            return handle_edit_post(mgr, varasto_id, data)
        return render_template(
            "edit.html", varasto_id=varasto_id, data=data
        )


def handle_edit_post(mgr, varasto_id, data):
    nimi = request.form.get("nimi", "").strip()
    tilavuus = parse_float(request.form.get("tilavuus", 0))
    result = mgr.update(varasto_id, nimi, tilavuus)
    if not result:
        flash("Virhe: Anna kelvollinen nimi ja kapasiteetti.", "error")
        return render_template("edit.html", varasto_id=varasto_id, data=data)
    return redirect(url_for("warehouse", varasto_id=varasto_id))


def register_delete_route(app):
    @app.route("/warehouse/<int:varasto_id>/delete", methods=["POST"])
    def delete_warehouse(varasto_id):
        mgr = get_manager(app)
        mgr.delete(varasto_id)
        return redirect(url_for("index"))


def register_routes(app):
    register_index_route(app)
    register_create_route(app)
    register_view_route(app)
    register_add_route(app)
    register_remove_route(app)
    register_edit_route(app)
    register_delete_route(app)


def create_app():
    app = Flask(__name__)
    app.secret_key = "dev-secret-key"
    register_routes(app)
    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run()
