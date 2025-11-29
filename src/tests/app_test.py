import unittest
from app import create_app, get_manager, WarehouseManager, parse_float


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        mgr = get_manager(self.app)
        mgr.reset()

    def get_mgr(self):
        return get_manager(self.app)

    def test_index_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Varastot", response.data)

    def test_create_page_loads(self):
        response = self.client.get("/create")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Luo uusi varasto", response.data)

    def test_create_warehouse(self):
        response = self.client.post("/create", data={
            "nimi": "Test Warehouse",
            "tilavuus": "100",
            "alku_saldo": "50"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Warehouse", response.data)

    def test_create_warehouse_invalid_shows_error(self):
        response = self.client.post("/create", data={
            "nimi": "",
            "tilavuus": "100",
            "alku_saldo": "50"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Virhe", response.data)

    def test_view_warehouse(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.get("/warehouse/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test", response.data)

    def test_view_nonexistent_warehouse_redirects(self):
        response = self.client.get("/warehouse/999", follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_add_products(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.post("/warehouse/1/add", data={
            "maara": "20"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(self.get_mgr().get(1)["varasto"].saldo, 70)

    def test_remove_products(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.post("/warehouse/1/remove", data={
            "maara": "20"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(self.get_mgr().get(1)["varasto"].saldo, 30)

    def test_edit_warehouse_page_loads(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.get("/warehouse/1/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Muokkaa", response.data)

    def test_edit_nonexistent_warehouse_redirects(self):
        response = self.client.get("/warehouse/999/edit", follow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_edit_warehouse(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.post("/warehouse/1/edit", data={
            "nimi": "Updated Name",
            "tilavuus": "200"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_mgr().get(1)["nimi"], "Updated Name")

    def test_edit_warehouse_invalid_shows_error(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.post("/warehouse/1/edit", data={
            "nimi": "",
            "tilavuus": "200"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Virhe", response.data)

    def test_delete_warehouse(self):
        self.get_mgr().create("Test", 100, 50)
        response = self.client.post("/warehouse/1/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.get_mgr().get(1))


class TestWarehouseManager(unittest.TestCase):
    def setUp(self):
        self.mgr = WarehouseManager()

    def test_create_warehouse(self):
        varasto_id = self.mgr.create("Test", 100, 50)
        self.assertEqual(varasto_id, 1)
        self.assertIsNotNone(self.mgr.get(varasto_id))

    def test_create_warehouse_invalid_name(self):
        varasto_id = self.mgr.create("", 100, 50)
        self.assertIsNone(varasto_id)

    def test_create_warehouse_invalid_tilavuus(self):
        varasto_id = self.mgr.create("Test", 0, 50)
        self.assertIsNone(varasto_id)

    def test_update_warehouse(self):
        varasto_id = self.mgr.create("Test", 100, 50)
        result = self.mgr.update(varasto_id, "Updated", 200)
        self.assertTrue(result)
        self.assertEqual(self.mgr.get(varasto_id)["nimi"], "Updated")

    def test_update_nonexistent_warehouse(self):
        result = self.mgr.update(999, "Test", 100)
        self.assertFalse(result)

    def test_update_warehouse_invalid_name(self):
        varasto_id = self.mgr.create("Test", 100, 50)
        result = self.mgr.update(varasto_id, "", 100)
        self.assertFalse(result)

    def test_update_warehouse_saldo_adjusted(self):
        varasto_id = self.mgr.create("Test", 100, 80)
        self.mgr.update(varasto_id, "Updated", 50)
        self.assertAlmostEqual(self.mgr.get(varasto_id)["varasto"].saldo, 50)

    def test_delete_warehouse(self):
        varasto_id = self.mgr.create("Test", 100, 50)
        result = self.mgr.delete(varasto_id)
        self.assertTrue(result)
        self.assertIsNone(self.mgr.get(varasto_id))

    def test_delete_nonexistent_warehouse(self):
        result = self.mgr.delete(999)
        self.assertFalse(result)

    def test_get_all(self):
        self.mgr.create("Test1", 100, 50)
        self.mgr.create("Test2", 200, 100)
        all_warehouses = self.mgr.get_all()
        self.assertEqual(len(all_warehouses), 2)

    def test_reset(self):
        self.mgr.create("Test", 100, 50)
        self.mgr.reset()
        self.assertEqual(len(self.mgr.get_all()), 0)
        self.assertEqual(self.mgr.next_id, 1)


class TestParseFloat(unittest.TestCase):
    def test_parse_valid_float(self):
        self.assertAlmostEqual(parse_float("3.14"), 3.14)

    def test_parse_valid_int(self):
        self.assertAlmostEqual(parse_float("42"), 42.0)

    def test_parse_invalid_returns_default(self):
        self.assertAlmostEqual(parse_float("abc"), 0.0)

    def test_parse_none_returns_default(self):
        self.assertAlmostEqual(parse_float(None), 0.0)

    def test_parse_custom_default(self):
        self.assertAlmostEqual(parse_float("abc", 5.0), 5.0)
