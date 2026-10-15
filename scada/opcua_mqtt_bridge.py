"""
Puente OPC UA <-> MQTT para el ABB IRB 140 (IRC5 + ABB IoT Gateway).

- Se conecta al servidor OPC UA del IoT Gateway (o del IRC5 OPC UA Server).
- Busca por nombre las variables PERS del módulo ModSCADA (scJ1 ... scCmd).
- Publica cada cambio en MQTT:  <base>/<variable>   y el estado completo en <base>/estado (JSON).
- Escribe en el robot lo que llegue a  <base>/cmd/<variable>  (solo variables permitidas).

Requisitos:  pip install asyncua paho-mqtt
Ejemplo:
    python opcua_mqtt_bridge.py --endpoint opc.tcp://192.168.0.50:61510/ABB.IRC5.OPCUA.Server \
        --broker 127.0.0.1 --base labsir/irb140/robot1

La primera conexión es rechazada por el IoT Gateway: en "IoT Gateway Configuration ->
Client Certificates" mueva el certificado de este cliente de "Rejected" a "Trusted" y vuelva a ejecutar.
"""
import argparse
import asyncio
import json
import logging
import socket
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from asyncua import Client, ua
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID

LECTURA = ["scJ1", "scJ2", "scJ3", "scJ4", "scJ5", "scJ6", "scX", "scY", "scZ",
           "scEstado", "scRutina", "scCiclos", "scCmd", "scRepeticiones"]
ESCRITURA = ["scCmd", "scRepeticiones"]          # lo único que el SCADA puede modificar
APP_URI = "urn:labsir:irb140:opcua-mqtt-bridge"

log = logging.getLogger("puente")


async def asegurar_certificado(carpeta: Path) -> tuple[Path, Path]:
    """Crea un certificado de aplicación propio si no existe (el servidor exige Sign o SignAndEncrypt)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    cert, key = carpeta / "cliente_cert.der", carpeta / "cliente_key.pem"
    if not cert.exists() or not key.exists():
        await setup_self_signed_certificate(
            key, cert, APP_URI, socket.gethostname(),
            [ExtendedKeyUsageOID.CLIENT_AUTH],
            {"countryName": "CO", "organizationName": "UNAL LabSIR", "commonName": "IRB140 OPCUA-MQTT bridge"})
        log.info("Certificado creado en %s", carpeta)
    return cert, key


async def buscar_nodos(raiz, nombres, profundidad=10):
    """Recorre el espacio de direcciones y devuelve {BrowseName: nodo} para las variables pedidas."""
    pendientes, encontrados = [(raiz, 0)], {}
    while pendientes and len(encontrados) < len(nombres):
        nodo, nivel = pendientes.pop()
        if nivel > profundidad:
            continue
        for hijo in await nodo.get_children():
            nombre = (await hijo.read_browse_name()).Name
            if nombre in nombres and nombre not in encontrados:
                if await hijo.read_node_class() == ua.NodeClass.Variable:
                    encontrados[nombre] = hijo
                    continue
            pendientes.append((hijo, nivel + 1))
    return encontrados


class Manejador:
    """Recibe los cambios de la suscripción OPC UA y los publica en MQTT."""

    def __init__(self, mqttc, base, nombres_por_nodo):
        self.mqttc, self.base, self.nombres = mqttc, base, nombres_por_nodo
        self.estado = {}

    def datachange_notification(self, nodo, valor, _dato):
        nombre = self.nombres.get(nodo.nodeid)
        if nombre is None:
            return
        if isinstance(valor, float):        # RAPID num llega como Float de 32 bits
            valor = round(valor, 3)
        self.estado[nombre] = valor
        self.mqttc.publish(f"{self.base}/{nombre}", json.dumps(valor), qos=0, retain=True)
        self.mqttc.publish(f"{self.base}/estado",
                           json.dumps({"t": round(time.time(), 3), **self.estado}), qos=0, retain=True)


async def puente(args):
    cert, key = await asegurar_certificado(Path(args.certs))
    cliente = Client(url=args.endpoint, timeout=10)
    cliente.application_uri = APP_URI
    if args.user:
        cliente.set_user(args.user)
        cliente.set_password(args.password or "")
    await cliente.set_security_string(f"{args.policy},{args.mode},{cert},{key}")

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"irb140-bridge-{socket.gethostname()}")
    mqttc.will_set(f"{args.base}/puente", "desconectado", retain=True)
    mqttc.connect(args.broker, args.port, keepalive=30)
    mqttc.loop_start()

    async with cliente:
        log.info("Conectado a %s", args.endpoint)
        nodos = await buscar_nodos(cliente.nodes.objects, set(LECTURA))
        faltan = sorted(set(LECTURA) - set(nodos))
        if faltan:
            log.warning("No se encontraron en el servidor: %s (¿están en el alias y son PERS?)", ", ".join(faltan))
        nombres_por_nodo = {n.nodeid: nombre for nombre, n in nodos.items()}
        tipos = {nombre: await nodos[nombre].read_data_type_as_variant_type()
                 for nombre in ESCRITURA if nombre in nodos}

        bucle = asyncio.get_running_loop()

        def al_recibir(_c, _u, msg):
            nombre = msg.topic.rsplit("/", 1)[-1]
            if nombre not in tipos:
                log.warning("Escritura rechazada: %s no es una variable de escritura", nombre)
                return
            try:
                valor = json.loads(msg.payload.decode())
            except ValueError:
                log.warning("Carga no válida en %s: %r", msg.topic, msg.payload)
                return
            vt = tipos[nombre]
            if vt in (ua.VariantType.Float, ua.VariantType.Double):
                valor = float(valor)
            elif vt != ua.VariantType.Boolean:
                valor = int(valor)
            asyncio.run_coroutine_threadsafe(
                nodos[nombre].write_value(ua.DataValue(ua.Variant(valor, vt))), bucle)
            log.info("SCADA -> robot: %s = %s", nombre, valor)

        mqttc.on_message = al_recibir
        mqttc.subscribe(f"{args.base}/cmd/+")
        mqttc.publish(f"{args.base}/puente", "conectado", retain=True)

        sub = await cliente.create_subscription(args.periodo, Manejador(mqttc, args.base, nombres_por_nodo))
        await sub.subscribe_data_change(list(nodos.values()))
        log.info("Publicando %d variables en %s/... (Ctrl+C para salir)", len(nodos), args.base)
        while True:
            await asyncio.sleep(5)
            await cliente.check_connection()


def main():
    p = argparse.ArgumentParser(description="Puente OPC UA (ABB IoT Gateway) <-> MQTT para el IRB 140")
    p.add_argument("--endpoint", default="opc.tcp://localhost:61510/ABB.IRC5.OPCUA.Server")
    p.add_argument("--policy", default="Basic256Sha256")
    p.add_argument("--mode", default="SignAndEncrypt", choices=["Sign", "SignAndEncrypt"])
    p.add_argument("--user", help="usuario OPC UA (si el servidor no acepta anónimo)")
    p.add_argument("--password")
    p.add_argument("--certs", default="certs", help="carpeta para el certificado del cliente")
    p.add_argument("--broker", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--base", default="labsir/irb140/robot1", help="prefijo de los tópicos MQTT")
    p.add_argument("--periodo", type=int, default=200, help="intervalo de publicación OPC UA [ms]")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    while True:
        try:
            asyncio.run(puente(args))
        except KeyboardInterrupt:
            break
        except Exception as e:  # reconexión simple ante caídas de red o del servidor
            log.error("Conexión perdida (%s). Reintentando en 5 s...", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
