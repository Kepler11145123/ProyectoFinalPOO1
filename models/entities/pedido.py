class Pedido:
    def __init__(self, id_pedido, id_cliente, data_pedido, status):
        self.id_pedido = id_pedido
        self.id_cliente = id_cliente
        self.data_pedido = data_pedido
        self.status = status


class DetallePedido:
    def __init__(self, id_detalle, id_pedido, id_producto, cantidad):
        self.id_detalle = id_detalle
        self.id_pedido = id_pedido
        self.id_producto = id_producto
        self.cantidad = cantidad