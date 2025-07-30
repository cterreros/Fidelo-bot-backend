# 📐 Documento de Diseño del Sistema (DDS) – FideloBot

---

## 1. Propósito

Este documento describe la arquitectura técnica del proyecto FideloBot, sus componentes principales, cómo se comunican 
entre sí y cómo se estructura el código para facilitar su evolución como librería y/o sistema SaaS.

---

## 2. Arquitectura general

FideloBot se basa en una arquitectura modular que incluye:

- Un backend Django + DRF para exponer la lógica de negocio mediante API REST.
- Un bot de mensajería (Telegram inicialmente) que interactúa con los usuarios finales.
- Un motor de cálculo de puntos desacoplado, con potencial de convertirse en una librería (`fidelo-core`).
- Un sistema de tareas programadas (cumpleaños, campañas) basado en APScheduler o Celery.
- Una base de datos PostgreSQL.

---

## 3. Componentes del sistema

### 3.1 Backend API (Django + DRF)

Responsable de gestionar:

- CRUD de Clientes, Negocios y Compras.
- Lógica de puntos (a través de servicios).
- Autenticación y permisos (si se implementa panel).
- Exposición de endpoints a otros clientes (como el bot).

> 📁 Apps esperadas:
> - `clientes/`, `compras/`, `puntos/`, `core/`, `api/`

---

### 3.2 Bot (Telegram)

Responsable de interactuar con el usuario (cliente final).  
Puede operar vía polling o webhooks y llama a los endpoints del backend o directamente a funciones de la librería 
`fidelo`.

> Comandos principales:
> - `/registrar_compra`, `/puntos`, `/cumpleaños`

---

### 3.3 Librería de lógica de fidelización (`fidelo-core`)

Encapsula reglas reutilizables:
```python
# fidelo/puntos.py

def calcular_puntos(monto):
    return monto // 10

def bonus_por_cumple():
    return 50
 ```
## 🔗 Diagrama entidad-relación

## 🔗 Diagrama entidad-relación

Puedes visualizar el modelo de entidades directamente en draw.io:

- 📄 Archivo editable: [`docs/fidelo_diagrama.drawio`](fidelo_diagrama.drawio)

> También se recomienda exportarlo como PNG o PDF para vistas rápidas (`docs/fidelo_diagrama.png`).

### 🧭 Cómo abrir el archivo `.drawio`

#### Si estás en PyCharm:
PyCharm no abre `.drawio` directamente. Abre el archivo así:

1. Ve a [https://app.diagrams.net](https://app.diagrams.net)
2. Haz clic en **Archivo > Abrir desde > Dispositivo...**
3. Selecciona el archivo desde la carpeta `docs/`
4. Edita el diagrama y guarda

Luego puedes subir los cambios o exportarlo como imagen.

