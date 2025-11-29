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
