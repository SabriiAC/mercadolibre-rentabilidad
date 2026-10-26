# Simulador de Rentabilidad y Retail Arbitrage en Mercado Libre Argentina

Proyecto de portfolio enfocado en responder una pregunta comercial concreta: **si una persona quiere empezar a revender tecnología en Mercado Libre con poco capital, ¿en qué categoría le conviene entrar y en cuál no?**

En e-commerce muchas veces se mira solo el precio de venta y se asume un margen fijo. En la práctica, entre la comisión de la plataforma, el costo fijo por unidad, los envíos obligatorios y el costo de reposición, un producto que parece rentable en los papeles puede terminar dando pérdida.

---

##  De dónde salieron los datos y cómo los procesé

En lugar de usar un dataset genérico de internet, decidí recolectar datos reales de Mercado Libre sobre 8 categorías de tecnología:
* Cargadores de pared
* Cables USB
* Soportes para notebook
* Auriculares inalámbricos
* Smartwatches
* Parlantes Bluetooth
* Powerbanks
* Teclados mecánicos

### Extracción e ingesta
Descargué las publicaciones con una extensión de scraping en el navegador, obteniendo 8 archivos CSV (uno por cada categoría) con más de 3.600 publicaciones en bruto.

Con un script de Python (`01_extraer_datos_simulador.py`) unifiqué los 8 archivos leyendo las etiquetas HTML de la página (por ejemplo `andes-money-amount__fraction` para el precio de lista y `fraction 2` para ofertas) para consolidar todo en una sola base cruda y auditar filas incompletas.

### Limpieza y calidad de datos con Pandas (`02_limpieza.py`)
Los datos crudos tenían varios errores típicos de scraping que corregí con Python:
* **Escala de precios rota:** Por problemas de formato con los puntos y comas, algunos precios quedaban mal formateados (por ejemplo, un producto de $68.000 figuraba como 68). Creé una función para detectar esos valores y corroborarlos con la publicacion, una vez confirmado se multiplican por 1.000 y recuperar el valor real en pesos.
* **Duplicados:** Al raspar varias páginas de resultados se repetían publicaciones. Dedupliqué por título y categoría, quedando una base final limpia de **2.599 publicaciones únicas**.
* **Clasificación de vendedores:** Separé a los vendedores particulares de las tiendas oficiales o marcas grandes.

---

## El modelo de costos: reglas reales de Mercado Libre (`03_modelo_financiero.py`)

Para calcular la rentabilidad neta no inventé márgenes. Me basé en la normativa oficial del portal de vendedores de Mercado Libre Argentina (guía de costos #870):

* **Comisión por venta:** 14,5% para publicaciones Clásicas y 29,5% para publicaciones Premium (las que ofrecen cuotas sin interés).
* **Costo fijo:** Mercado Libre cobra un cargo fijo extra de $1.100 por cada unidad vendida que cueste menos de $30.000.
* **Envío gratis obligatorio:** Si el producto supera los $30.000, la plataforma obliga al vendedor a dar envío gratis. El vendedor debe absorber una tarifa de flete bonificada ($3.800 para productos chicos y $4.800 para productos con más volumen como teclados o parlantes).
* **Costo de compra estimado:** Estimé el costo de compra mayorista o de importación de referencia por categoría (entre el 25% y 38% del precio de venta).

Con estos parámetros calculé la **ganancia neta en pesos**, el **margen neto porcentual** y el **retorno sobre la inversión (ROI %)** para cada una de las 2.599 publicaciones.

---

## Visualización en Power BI

![Dashboard Ejecutivo](dashboard_simulador.png)

Armé el dashboard interactivo en Power BI (`dashboard.pbix`) para facilitar la lectura de los datos.

### Criterios aplicados en el reporte:
* **Uso de medianas en vez de promedios:** En todas las medidas DAX principales usé la mediana. En marketplaces suele haber publicaciones con precios atípicos o combos gigantescos que inflan el promedio y dan una idea falsa del mercado. La mediana muestra la venta típica.
* **Comparativa financiera unitaria:** El gráfico de columnas agrupa el precio de venta, el costo de compra y la ganancia neta en bolsillo por cada unidad vendida. Como categorías como cables USB ($15.000) comparten eje con smartwatches ($86.000), configuré etiquetas en miles para que los productos más accesibles no se pierdan a la vista.
* **Filtro interactivo:** Selector de categoría para analizar el comportamiento individual de cada nicho.

---

##  Conclusiones y recomendaciones comerciales

Al cruzar margen neto, nivel de competencia de tiendas oficiales y costos de envío, encontré 5 conclusiones claras:

1. **Cargadores de pared (La mejor oportunidad de entrada):** Es el nicho más conveniente para alguien que empieza. Presenta un margen neto mediano del 48% y un ROI del 160%, y en la muestra analizada no encontré marcas ni tiendas oficiales compitiendo de forma masiva (0%).
2. **Soportes para notebook (Ventaja en logística):** Como la gran mayoría cuesta menos del umbral de $30.000, el comprador paga el flete en el 43% de las ventas. Esto evita que el vendedor tenga que absorber el costo del envío y cuida un margen neto del 39%.
3. **Cables USB (Margen alto pero ticket bajo):** Tienen el porcentaje de ganancia más alto (52%), pero como el ticket mediano ronda los $15.000, el cargo fijo de $1.100 por venta golpea fuerte vendiendo de a una unidad. La recomendación comercial es venderlos en combos de 2 o 3 unidades para diluir ese costo fijo.
4. **Powerbanks y Parlantes (Atención al flete obligatorio):** Tienen márgenes aceptables (38% a 43%), pero como casi todos superan los $30.000, el vendedor queda obligado a financiar el envío gratis, reduciendo la ganancia final.
5. **Teclados mecánicos (Categoría a evitar):** Es el mercado más difícil para un vendedor particular. Deja el margen más bajo (28%), el 79% del catálogo está dominado por marcas establecidas (Logitech, Redragon) y la mayoría compite ofreciendo cuotas sin interés, lo que obliga a pagar la comisión más cara de 29,5%.

---

##  Estructura del repositorio

* `dashboard.pbix`: Archivo de Power BI Desktop con el modelo de datos, medidas DAX y visualizaciones.
* `dashboard_simulador.png`: Captura de pantalla en alta resolución del reporte.
* `SCRIPTS`: Carpeta con los scripts de Python:
  * `01_extraer_datos_simulador.py`: Ingesta y consolidación de los archivos por categoría.
  * `02_limpieza.py`: Limpieza de formatos, corrección de escalas y duplicados.
  * `03_modelo_financiero.py`: Cálculo de comisiones, fletes, costo FOB y márgenes.
* `simulador_meli_dataset_final.csv`: Dataset final limpio con 2.599 publicaciones procesadas.
