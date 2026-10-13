# BiblioPer: Sistema de Gestión de Biblioteca

## 1. Nombre y descripción breve del sistema

**BiblioPer** es un sistema web de gestión de biblioteca pensado para bibliotecas pequeñas y universitarias. Centraliza el catálogo de libros, los usuarios y los préstamos en un único sistema, y automatiza el control de disponibilidad, vencimientos y multas, reemplazando el uso de cuadernos u hojas de cálculo.

**Problemas que resuelve:**

- Pérdida o duplicación de información sobre el inventario.
- Dificultad para saber qué libros están disponibles o prestados.
- Préstamos vencidos sin seguimiento ni cobro de multas.
- Largas filas y tiempos de espera para consultar o reservar un libro.
- Falta de reportes para la toma de decisiones (libros más solicitados, usuarios morosos).

**Usuarios del sistema:**

| Usuario | Descripción |
|---|---|
| Administrador | Gestiona el sistema, los bibliotecarios, los parámetros (días de préstamo, valor de la multa) y los reportes. |
| Bibliotecario | Registra libros, usuarios, préstamos, devoluciones y multas. |
| Lector (socio) | Consulta el catálogo, reserva libros y revisa su historial de préstamos. |

## 2. Integrantes del equipo

**Grupo 7**

- Edder Alexander Robayo
- Jeremy Hernandez Tutistar
- Santiago Lazo Villarraga

**Docente:** Juan Camilo Olarte Betancourt

Universidad Tecnológica de Pereira · Facultad de Ingenierías · Programa Tecnología en Desarrollo de Software

## 3. Funcionalidades principales

1. Autenticación y control de acceso por rol.
2. Gestión del catálogo de libros (crear, editar, eliminar y buscar).
3. Gestión de usuarios y socios.
4. Registro de préstamos y devoluciones.
5. Reserva de libros no disponibles.
6. Cálculo automático de multas por retraso.
7. Consulta del catálogo y del historial personal.
8. Reportes de préstamos activos, libros más prestados y morosos.

**Reglas de negocio principales:** un lector puede tener máximo 3 préstamos activos, el plazo de préstamo es de 7 días y no se prestan libros a lectores con multas pendientes.

## 4. Tecnologías utilizadas

| Capa | Responsabilidad | Tecnología |
|---|---|---|
| Presentación (frontend) | Interfaz de usuario | HTML5, CSS3, JavaScript (Fetch API) |
| API y negocio (backend) | Reglas de préstamos, multas y reservas | Python, FastAPI |
| Acceso a datos | ORM y validación de esquemas | SQLAlchemy, Pydantic |
| Datos | Persistencia | SQLite |
| Control de versiones | Trabajo colaborativo | Git y GitHub |

**Arquitectura:** cliente-servidor en capas con API REST. El navegador consume una API (capa de presentación) que delega en la lógica de negocio (servicios), la cual accede a los datos mediante un ORM sobre una base de datos relacional. La lógica de negocio también usa un servicio de correo para las notificaciones.

## 5. Estructura del proyecto

```
sistema-biblioteca/
├── backend/
│   ├── app/
│   │   ├── database.py      # Configuración y conexión de SQLAlchemy
│   │   ├── models.py        # Modelos de tablas de la base de datos
│   │   ├── schemas.py       # Esquemas de validación de Pydantic
│   │   ├── crud.py          # Operaciones directas a la base de datos
│   │   └── main.py          # Punto de entrada de FastAPI y rutas
│   ├── requirements.txt     # Dependencias del proyecto Python
│   └── biblioteca.db        # Base de datos SQLite (generada automáticamente)
│
└── frontend/
    ├── css/
    │   └── styles.css       # Hoja de estilos global
    ├── js/
    │   ├── api.js           # Funciones modularizadas con Fetch API
    │   └── app.js           # Manejo del DOM y eventos
    └── index.html           # Interfaz principal de usuario
```

## 6. Instrucciones de instalación y ejecución

### Requisitos previos

- Python 3.10 o superior
- Git
- Un navegador moderno (Chrome, Firefox o Edge)

### Instalación

1. Clonar el repositorio:

   ```bash
   git clone <URL-DEL-REPOSITORIO>
   cd biblioper
   ```

2. Crear y activar un entorno virtual:

   ```bash
   cd backend
   python -m venv venv

   # Linux / macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

### Ejecución del backend

Desde la carpeta `backend/`:

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000` y la documentación interactiva en `http://127.0.0.1:8000/docs`. El archivo `biblioteca.db` se genera automáticamente en el primer arranque.

### Ejecución del frontend

Desde la carpeta `frontend/`, abrir `index.html` en el navegador o, preferiblemente, servirlo con un servidor local:

```bash
python -m http.server 5500
```

Luego ingresar a `http://localhost:5500`.

## 7. Estrategia de ramas y convención de commits

### Estrategia de ramas

| Rama | Propósito |
|---|---|
| `main` | Código estable y listo para entregar. Solo recibe cambios desde `develop`. |
| `develop` | Rama de integración donde se unen las funcionalidades terminadas. |
| `feature/<nombre>` | Una rama por funcionalidad (por ejemplo, `feature/prestamos`). Se crea desde `develop`. |
| `fix/<nombre>` | Corrección de errores. Se crea desde `develop`. |

Flujo de trabajo: crear la rama desde `develop`, hacer commits pequeños, abrir un Pull Request hacia `develop` y fusionar después de que otro integrante lo revise.

### Convención de mensajes de commit

Formato: `tipo(alcance): descripción corta en infinitivo`

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de errores |
| `docs` | Documentación |
| `refactor` | Mejora de código sin cambiar el comportamiento |
| `test` | Pruebas |

**Ejemplos:**

```
feat(prestamos): registrar préstamo validando disponibilidad
fix(multas): corregir cálculo de días de retraso
docs(readme): agregar instrucciones de instalación
refactor(crud): separar consultas de libros en funciones
test(prestamos): probar límite de 3 préstamos por lector
```
