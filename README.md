# Forecash – Backend

API REST del sistema **Forecash**, una plataforma para el análisis financiero, generación de dashboards interactivos, predicciones (ARIMA) y reportes automáticos para pequeños negocios.

## 🧱 Arquitectura

Módulos principales:

- **Autenticación (auth):** login, JWT, hashing con bcrypt, control de acceso por rol (super administrador, representante legal, usuario estándar).
- **Empresas y usuarios:** registro de solicitudes, aprobación/rechazo, modelo multi-empresa mediante tabla pivote.
- **Carga y validación de datos:** importación de archivos CSV/XLSX, validación de estructura y formato.
- **Análisis descriptivo:** cálculo de KPIs (ingresos, gastos, margen, ventas por periodo, flujo de caja) y generación de datos para gráficos.
- **Modelo predictivo (ARIMA):** entrenamiento automático de modelos de series temporales con `pmdarima` (auto_arima) y generación de predicciones.
- **Generación de reportes:** creación de reportes en PDF con la información de empresa, periodo y usuario.
- **Validación, ORM y auditoría:** validación con Pydantic v2, persistencia con SQLAlchemy 2.x, registro de acciones con timestamp.

## 🛠️ Stack tecnológico

| Capa     | Tecnología                  | Versión          |
|----------|------------------------------|-------------------|
| Lenguaje | Python                        | 3.11 / 3.13       |
| Framework| FastAPI                       | 0.109.2           |
| Servidor | Uvicorn                        | 0.27.1            |
| Validación / config | Pydantic / pydantic-settings | 2.12.5 / 2.6.1 |
| ORM      | SQLAlchemy                    | 2.0.29            |
| Migraciones | Alembic                     | 1.13.1            |
| Base de datos | PostgreSQL (psycopg2-binary) | -              |
| Datos    | Pandas / NumPy                 | 2.2.1 / 1.26.4    |
| Series temporales | Statsmodels / pmdarima | 0.14.1 / 2.0.4   |
| Machine learning | scikit-learn / scipy   | 1.4.1 / 1.13.0    |
| Visualización (reportes) | Matplotlib / Seaborn | 3.8.4 / 0.13.2 |
| Reportes PDF | WeasyPrint      | 4.1.0 / 62.3      |
| Autenticación | python-jose / PyJWT        | 3.3.0 / 2.8.0     |
| Hash de contraseñas | Passlib + bcrypt        | 1.7.4 / 4.1.2     |
| Archivos | openpyxl                       | 3.1.2             |
| Correo   | fastapi-mail / aiosmtplib       | 1.6.2 / 5.1.0     |
| Almacenamiento / Auth externo | Firebase Admin    | 6.5.0             |
| Pruebas  | pytest / pytest-asyncio          | 7.4.4 / 0.23.6    |
| Documentación API | Swagger UI (FastAPI)      | integrado         |

## 📂 Estructura del proyecto

```
app/
├── api/
│   ├── routes/            # Endpoints (auth, company, dataset, predictions, reports, request, user)
│   └── router.py          # Router principal que agrupa todas las rutas
├── core/
│   ├── db/                 # Configuración de base de datos (engine, sesión, base declarativa)
│   ├── firebase/            # Configuración de Firebase
│   ├── mail/                # Configuración de envío de correos
│   ├── config.py            # Configuración general / variables de entorno
│   └── security.py          # Hashing, JWT y utilidades de seguridad
├── dependencies/             # Dependencias de FastAPI (usuario actual, rol, empresa, super admin, etc.)
├── models/
│   ├── company/              # Empresa, sector económico, tipo de entidad, tipo de régimen
│   ├── dataset/              # Datasets crudos y registros (raw_dataset, raw_record)
│   ├── dimensions/            # Dimensiones del modelo analítico (fecha, producto, cliente, categoría, etc.)
│   ├── fact/                  # Tabla de hechos (fact_operation)
│   ├── request/               # Solicitudes de registro y archivos
│   ├── user/                   # Usuario, roles y tipos de documento
│   ├── user_company/            # Tabla pivote usuario-empresa y roles por empresa
│   └── refresh_token.py
├── schemas/
│   ├── request_schema/        # Esquemas de entrada (auth, predicciones, registro, configuración tributaria, etc.)
│   └── response_schema/       # Esquemas de salida (auth, empresas, datasets, predicciones, usuarios, etc.)
├── scripts/                    # Scripts utilitarios (creación de superadmin, pruebas de conexión, correo, series)
├── services/
│   ├── auth/                   # Login y manejo de refresh tokens
│   ├── company/                # Lógica de negocio de empresas
│   ├── datasets/                 # ETL, mapeo de columnas, dimensiones, métricas y drill-down
│   ├── email/                    # Envío de correos electrónicos
│   ├── forecasting/               # Servicio de predicción (ARIMA)
│   ├── reports/                    # Generación de reportes PDF (plantillas y assets)
│   ├── requests/                    # Gestión de solicitudes de registro
│   └── users/                        # Lógica de negocio de usuarios
└── main.py                      # Punto de entrada de la aplicación FastAPI
```

## ⚙️ Requisitos previos

- Python 3.13 o superior
- PostgreSQL 17
- pip / virtualenv

## 🚀 Instalación y ejecución local

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/<usuario>/forecash-backend.git
   cd forecash-backend
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate   # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:

   Crear un archivo `.env` en la raíz del proyecto (este archivo está excluido del repositorio) con, por ejemplo:

   ```env
   # Base de datos
   DATABASE_URL=postgresql://usuario:password@localhost:5432/forecash

   # Seguridad / JWT
   SECRET_KEY=tu_clave_secreta
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=480

   # Correo (fastapi-mail)
   MAIL_USERNAME=tu_correo@ejemplo.com
   MAIL_PASSWORD=tu_password
   MAIL_FROM=tu_correo@ejemplo.com
   MAIL_PORT=587
   MAIL_SERVER=smtp.ejemplo.com

   # Firebase
   FIREBASE_CREDENTIALS_PATH=ruta/a/credenciales-firebase.json
   ```

   > ⚠️ **WeasyPrint** requiere dependencias del sistema (Pango, Cairo, GDK-PixBuf) para la generación de reportes PDF. En sistemas basados en Debian/Ubuntu pueden instalarse con:
   >
   > ```bash
   > sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
   > ```

5. Ejecutar las migraciones de la base de datos:

   ```bash
   alembic upgrade head
   ```

6. Levantar el servidor de desarrollo:

   ```bash
   uvicorn app.main:app --reload
   ```

La API quedará disponible en `http://localhost:8000`.

## 📑 Documentación de la API

FastAPI genera automáticamente la documentación interactiva (Swagger UI):

- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

Cada endpoint incluye descripción, parámetros, tipos de respuesta, ejemplos y códigos de error documentados (400, 401, 403, 404, 422, 500).

## 🔐 Seguridad

- Autenticación mediante **JWT** (access token con expiración de 8 horas).
- Contraseñas almacenadas con **hash bcrypt** (Passlib), nunca en texto plano.
- Control de acceso basado en roles: super administrador, representante legal, usuario estándar.
- Acceso a la base de datos exclusivamente mediante ORM (SQLAlchemy) con queries parametrizadas (sin SQL crudo).
- Variables sensibles gestionadas mediante archivo `.env` (excluido del control de versiones).
- Registro de auditoría de las acciones de los usuarios con timestamp.

## 📊 Funcionalidades principales

- Importación y validación de archivos CSV/XLSX.
- Cálculo de indicadores financieros (ingresos, gastos, margen de ganancia, ventas por periodo, flujo de caja).
- Generación de datos para visualizaciones (líneas, barras, histogramas, dispersión) y soporte de drill-down.
- Entrenamiento automático de modelos ARIMA (selección automática de parámetros p, d, q con `auto_arima`) y generación de predicciones para periodos definidos por el usuario.
- Generación de reportes automáticos en PDF.
- Gestión de solicitudes de registro de empresas y usuarios, con soporte multi-empresa.

## 🧪 Pruebas

```bash
pytest
```

## 🌳 Flujo de trabajo (Git)

- Rama principal `main` protegida.
- Desarrollo mediante ramas por feature (`feature/nombre-funcionalidad`).
- Metodología de trabajo: XP + Kanban.

## 👥 Autores

Gina Paola Moreno Caicedo - Junior Full Stack Developer
