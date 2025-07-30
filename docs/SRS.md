# 📄 Documento de Especificación de Requisitos (SRS) – FideloBot

---

## 1. Introducción

### 1.1 Propósito del sistema

FideloBot es una solución de fidelización para pequeños negocios que permite a sus clientes acumular puntos por sus compras, consultar su saldo de puntos y recibir bonificaciones automáticas por eventos especiales como cumpleaños, todo mediante un bot de mensajería (ej. Telegram).

---

### 1.2 Público objetivo

- Propietarios de pequeños negocios (minimarkets, cafeterías, estéticas, ferreterías).
- Que usen celular con apps como Telegram o WhatsApp.
- Que quieran fidelizar clientes sin software complicado.

---

### 1.3 Alcance del sistema (MVP)

- Registro de clientes y compras vía bot.
- Cálculo automático de puntos según monto de compra.
- Consulta de puntos por cliente.
- Mensaje automático de cumpleaños.
- Panel admin básico (opcional).

---

## 2. Requisitos del sistema

### 2.1 Requisitos funcionales

| ID | Descripción                                                                 |
|----|-----------------------------------------------------------------------------|
| RF1 | El sistema debe permitir registrar una compra con nombre y monto.         |
| RF2 | El sistema debe calcular automáticamente los puntos ganados.              |
| RF3 | El cliente debe poder consultar su saldo de puntos desde el bot.          |
| RF4 | El sistema debe enviar un mensaje automático de cumpleaños con bonus.     |
| RF5 | El administrador puede ver los clientes y puntos desde Django Admin.      |

---

### 2.2 Requisitos no funcionales

| ID  | Descripción                                                                 |
|-----|-----------------------------------------------------------------------------|
| RNF1 | El sistema debe responder en menos de 2 segundos al cliente.              |
| RNF2 | El backend debe soportar al menos 1000 clientes concurrentes.             |
| RNF3 | Los datos deben almacenarse de forma segura en PostgreSQL.                |
| RNF4 | El bot debe estar disponible el 95% del tiempo.                           |
| RNF5 | El sistema debe permitir futura integración con WhatsApp.                 |

---

## 3. Supuestos y restricciones

- El canal de interacción inicial será Telegram.
- Cada cliente pertenece a un solo negocio.
- Se asumirá que el número de celular es único por cliente.
- El MVP usará SQLite localmente, y PostgreSQL en producción.

---

## 4. Historias de usuario

```plaintext
Como cliente, quiero poder consultar mis puntos acumulados por el bot, para saber cuánto me falta para obtener un premio.

Como dueño de negocio, quiero registrar una compra desde el bot para que los puntos se acumulen automáticamente.

Como cliente, quiero recibir una felicitación en mi cumpleaños con puntos extra.

Como administrador, quiero ver desde el panel los clientes y sus puntos para hacer seguimiento.

Como desarrollador, quiero que la lógica de puntos esté separada en un módulo para poder reutilizarla como librería.
