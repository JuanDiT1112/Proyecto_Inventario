import streamlit as st
import pandas as pd
import os

# =========================
# CONFIGURACIÓN INICIAL
# =========================
st.set_page_config(page_title="Tuberías San Francisco - Inventario", layout="wide")

# Rutas de archivos
RUTA_LOGO = "logo.png"  # Coloca tu logo en esta ruta
RUTA_INVENTARIO = "data/inventario_actualizado.csv"

# Credenciales de usuarios
USUARIOS = {
    "admin": {"password": "decu1232", "rol": "Administrador"},
    "usuario": {"password": "1234", "rol": "Invitado"},
}

# =========================
# FUNCIÓN LOGIN
# =========================
def login():
    st.image(RUTA_LOGO, width=250)
    st.title("🔐 Sistema de Inventario - Tuberías San Francisco")
    st.write("---")

    usuario = st.text_input("Usuario")
    contrasena = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if usuario in USUARIOS and contrasena == USUARIOS[usuario]["password"]:
            st.session_state["usuario"] = usuario
            st.session_state["rol"] = USUARIOS[usuario]["rol"]
            st.success(f"Bienvenido {usuario} ({st.session_state['rol']})")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrecta")

# =========================
# FUNCIÓN PRINCIPAL INVENTARIO
# =========================
def app_inventario():
    st.sidebar.image(RUTA_LOGO, width=180)
    st.sidebar.title("Menú Principal")

    rol = st.session_state.get("rol", "Invitado")

    st.sidebar.write(f"👤 Usuario: {st.session_state['usuario']} ({rol})")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    st.title("📦 Inventario de Productos")

    # =========================
    # CARGAR INVENTARIO EXISTENTE
    # =========================
    if os.path.exists(RUTA_INVENTARIO):
        try:
            df = pd.read_csv(RUTA_INVENTARIO, encoding="utf-8")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(RUTA_INVENTARIO, encoding="latin1")
            except Exception as e:
                st.error(f"❌ Error al leer el archivo de inventario: {e}")
                df = pd.DataFrame(columns=["ID", "Nombre", "Categoría", "Subcategoría", "Precio", "Stock"])

        # ✅ Asegurar columnas faltantes
        for col in ["Precio", "Stock"]:
            if col not in df.columns:
                df[col] = 0
    else:
        df = pd.DataFrame(columns=["ID", "Nombre", "Categoría", "Subcategoría", "Precio", "Stock"])
        st.warning("No existe archivo de inventario guardado todavía.")

    # =========================
    # ADMIN: SUBIR NUEVO ARCHIVO CSV
    # =========================
    if rol == "Administrador":
        st.subheader("🔄 Actualizar Inventario")
        archivo = st.file_uploader("Sube un archivo CSV o Excel con los productos", type=["csv", "xlsx", "xls"])

        if archivo is not None:
            try:
                nombre_archivo = archivo.name.lower()

                if nombre_archivo.endswith(".csv"):
                    # Leer CSV con detección automática de separador
                    try:
                        nuevo_df = pd.read_csv(archivo, sep=None, engine="python", encoding="utf-8-sig")
                    except Exception:
                        # En caso de error, usar encoding alternativo
                        archivo.seek(0)
                        nuevo_df = pd.read_csv(archivo, sep=None, engine="python", encoding="latin1")

                elif nombre_archivo.endswith((".xlsx", ".xls")):
                    nuevo_df = pd.read_excel(archivo)

                else:
                    raise ValueError("Formato de archivo no soportado. Use CSV o Excel.")

                # Verificar columnas obligatorias
                columnas_necesarias = {"ID", "Nombre", "Categoría", "Subcategoría"}
                if not columnas_necesarias.issubset(nuevo_df.columns):
                    st.error("❌ El archivo debe contener las columnas: ID, Nombre, Categoría y Subcategoría.")
                    st.stop()

                # Agregar columnas faltantes
                for col in ["Precio", "Stock"]:
                    if col not in nuevo_df.columns:
                        nuevo_df[col] = 0

                # Guardar en el sistema
                nuevo_df.to_csv(RUTA_INVENTARIO, index=False, encoding="utf-8")
                df = nuevo_df
                st.success("✅ Inventario cargado correctamente y guardado en el sistema.")

            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {e}")

    # =========================
    # BUSCADOR DE PRODUCTOS
    # =========================
    st.subheader("🔍 Buscar producto")
    busqueda = st.text_input("Ingrese nombre, categoría o ID del producto")
    if busqueda:
        resultado = df[df.apply(lambda fila: fila.astype(str).str.contains(busqueda, case=False).any(), axis=1)]
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
        else:
            st.warning("No se encontraron productos con ese término de búsqueda.")
    else:
        st.dataframe(df, use_container_width=True)

    # =========================
    # ADMIN: MODIFICAR PRECIOS O STOCK
    # =========================
    if rol == "Administrador":
        st.subheader("✏️ Modificar precios o stock")
        producto_id = st.selectbox("Selecciona un producto", df["ID"].unique())

        if producto_id:
            fila = df[df["ID"] == producto_id].iloc[0]
            precio = st.number_input("Precio Unitario ($)", min_value=0.0, value=float(fila["Precio"]))
            stock = st.number_input("Cantidad en Stock", min_value=0, value=int(fila["Stock"]))

            # Calcular valor total automáticamente
            valor_total = precio * stock
            st.write(f"💰 **Valor total del producto:** ${valor_total:,.2f}")

            col1, col2 = st.columns(2)
            if col1.button("💾 Guardar cambios"):
                df.loc[df["ID"] == producto_id, "Precio"] = precio
                df.loc[df["ID"] == producto_id, "Stock"] = stock
                df.to_csv(RUTA_INVENTARIO, index=False, encoding="utf-8")
                st.success("✅ Cambios guardados correctamente.")
                st.rerun()

            if col2.button("❌ Cancelar cambios"):
                st.info("Cambios cancelados.")

# =========================
# FUNCIÓN PRINCIPAL
# =========================
def main():
    # Crear carpeta de datos si no existe
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("assets"):
        os.makedirs("assets")

    if "usuario" not in st.session_state:
        login()
    else:
        app_inventario()

if __name__ == "__main__":
    main()
