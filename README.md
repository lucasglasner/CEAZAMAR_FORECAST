# Pronóstico CEAZAMAR - Rutinas del oceanograma y plots varios

### Generalidades

La presente documentación muestra un resumen de los scripts y como usarlos para visualizar el pronóstico del ceazamar a nivel regional o local para un punto de interés. En primer lugar para tener un idea del funcionamiento del paquete se lista la estructura general de directorios con un breve comentario de que es cada cosa:

```bash
.
├── data				# Carpeta con carpetas a los datos netcdf crudos y datos estáticos varios 
│   ├── ASCAT				# Carpeta donde se descarga ASCAT diariamente
│   ├── COASTAL_POINTS.csv		# Tabla .csv con las localidades de interes para el oceanograma
│   ├── FORECAST			# Carpeta con pronósticos
│   │	├── MERCATOR			# Carpeta con netcdf pronosticos marinos (.nc tienen que tener la fecha en alguna parte de su nombre)
│   │	└── WRF 			# Carpeta con netcdf pronosticos atmosfericos (.nc tienen que tener la fecha en alguna parte de su nombre)
│   ├── OSTIA				# Carpeta con temperatura satelital
│   ├── regiones.gpkg			# Poligono con las regiones de Chile (para los mapas)
│   └── TPXO7.nc			# NetCDF con la amplitud y fase de las mareas
├── pytides				# Paquete de procesamiento de mareas en python (equivalente a MATLAB t-tide)
│   └── README.md
├── static				# Carpeta con imagenes estaticas para graficos (e.g logo del ceaza)
│   ├── Logo_Ceaza_blanco.png
│       ... ... ...
│   └── Logo_Ceaza_negro.png
├── plots				# Carpeta donde guardar los graficos generados con el paquete
│   ├── FORECAST_SITES			# Carpeta con figuras asociadas a pronosticos locales/puntuales
│   │   ├── CEAZAMAR			# Figuras del pronostico operacional (.png y .pdf)
│   │   │   ├── *.png
│   │   │       ... ... ...
│   │   │   └── *.pdf
│   │   ├── ... ... ...
│   │   └── *.png			# Figuras del pronostico de un punto de interes que no es del ceazamar operacional
│   ├── ... ... ...
│   └── *.png				# Figuras con mapas de pronostico regional
├── tmp					# Carpeta con las tablas .csv del oceanograma (se actualiza todos los días)
│   ├── ... ... ...
│   └── *.csv
├── params.py				# Archivo de control con los parametros y rutas a los datos
├── check_forecast_status.py		# Script para verificar que las figuras/tablas del pronóstico de hoy se hicieron bien
├── create_localforecast.py		# Script para crear la tabla del oceanograma
├── currents_forecast.py		# Script para hacer un plot de corrientes superficiales
├── local_forecast.py			# Script para hacer las figuras del oceanograma
├── local_forecast_print.py		# Script para transformar las figuras del oceanograma a .pdf imprimibles
├── nrt_forecast.py			# Script para hacer una figura del estado de la región "ahora" según la info del pronóstico
├── sst_diagnostics.py			# Script para hacer una figura con el diagnóstico de SST satelital
├── sst_forecast.py			# Script para hacer los mapas de pronóstico de SST
├── sst_validation.py			# Script para hacer los mapas de error del pronóstico SST
├── wave_diagnostics.py			# Script para hacer mapas con diagnóstico de oleaje
├── wave_forecast.py			# Script para hacer los mapas de pronóstico de oleaje
├── wind_diagnostics.py			# Script para hacer mapas con diagnóstico de viento
├── wind_forecast.py			# Script para hacer los mapas de pronóstico de viento
├── wind_validation.py			# Script para hacer mapas de error del pronóstico de viento
├── post_request.py			# Script para sincronizar/copiar datos y figuras hacia servidores remotos
├── run.py				# Script general para correr todos los scripts juntos
├── run.log				# Bitacora de lo que pasó al correr el script run.py (se genera con el cron)
├── numerics.py				# Listado de funciones/rutinas de cálculo numérico de cosas
├── graphical.py			# Listado de funciones/rutinas para graficar
├── load.py				# Listado de funciones/rutinas para leer la data cruda y transformarla a un formato común
├── forecast.yml			# Archivo con el ambiente python necesario para correr este paquete en Linux
└── README.md				# Archivo con esta documentación.
```

Todos los scripts están construidos siguiendo un formato python del siguiente estilo:

```python
import os
import sys
import ... as ...
from ... import ...

def method1(...):
    ...
    return ...

def method2(...):
    ...
    return ...

if __name__=='__main'__:
    ...
    method1(...)
    method2(...)
    sys.exit()
```

De esta forma se mantiene una estructura util para llamar a los metodos desde otros scripts, pero si el archivo se corre desde la consola se realizarán las instrucciones que están desde la línea con el if hacia abajo (línea 14 del ejemplo anterior).

Para que la ejecución de las rutinas funcione es fundamental que la ruta al python3 utilizado sea con un ejecutable asociado a un ambiente y paquetes correctos. Esto se puede verificar con los siguientes comandos:

```bash
which python3
conda list
pip list
```

El primer comando retornara la ruta al python3 disponible en la consola, mientras que los otros dos mostrarán una lista de los paquetes instalados con conda o con pip (gestores de paquetes). Para utilizar este programa recomiendo instalar un ambiente nuevo (en una maquina con linux) con el archivo *forecast.yml* que contiene los paquetes y ambiente python con el cual los scripts se programaron. (Para más detalles sobre como manejar ambientes virtuales ver el siguiente link de la documentación oficial [https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html]()).

El paquete fue construido con esta estructura para facilitar la creación de figuras con distintas fuentes de datos. Para esto el paquete funciona con tres tipos de pronósticos: (i) pronóstico atmosférico, (ii) pronóstico océanico y (iii) pronóstico de oleaje. El pronóstico océanico hace referencia a las variables de un modelo físico (temperatura, salinidad, corrientes, etc) diferenciandose del modelo de oleaje para más flexibilidad (usualmente son modelos distintos aunque para 2023 ya están en desarrollo los modelos acoplados). Actualmente el paquete está utilizando el modelo WRF de CEAZA como pronóstico atmosférico y los modelos globales de MERCATOR para la componente océanica y de oleaje. Para controlar que tipo de pronósticos se usan hay que editar el archivo *params.py* donde se especifíca la carpeta en donde se guardan los pronósticos de cada tipo, como también los nombres de las variables y otros parámetros generales de la visualización. Acá abajo se muestra un breve ejemplo de como se ven los parámetros generales del archivo.

```python
import datetime
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

FORECAST_DATE        = datetime.datetime.now().strftime('%F')		# Fecha de ahora mismo usando el tiempo de la máquina de trabajo
EXECUTION_DIRECTORY  = '/home/lucas/projects/CEAZAMAR_FORECAST/'   	# Directorio de trabajo
NDAYS_REGIONAL = 10							# Horizonte de pronóstico a considerar en los mapas (días)
NHOURS_LOCAL   = 24*9-12						# Horizonte de pronóstico a considerar en la visualización del oceanograma (horas)
N_JOBS = 10								# Número de núcleos para cálculos en paralelo

#LEADTIME MAPS GENERAL CONFIGURATION
landpolygon_path       = 'data/regiones.gpkg'				# Ruta al polígono con las regiones de Chile (para mejorar los mapas)
atm_mapsextent         = [-75,-70.8,-34,-28]				# Extensión geográfica de los mapas (lonmin, lonmax, latmin, latmax)
ocean_mapsextent       = [-75,-70.8,-34,-28]				# IDEM
wave_mapsextent        = [-75,-70.8,-34,-28]				# IDEM
diagnostics_mapsextent = [-75,-70.8,-34,-28]				# IDEM
```

y en el siguiente trozo de código como se ven los parámetros para el pronóstico océanico MERCATOR:

```python
# ---------------------------------------------------------------------------- #
#                                     OCEAN                                    #
# ---------------------------------------------------------------------------- #
ocean_model_name       = 'NEMO-Meteofrance'
ocean_validation_name  = 'OSTIA'
# ----------------------------------- paths ---------------------------------- #
ocean_tidemodel_file   = 'data/TPXO7.nc'
ocean_forecast_dir     = 'data/FORECAST/MERCATOR/PHYSICS'
ocean_hindcast_dir     = 'data/FORECAST/MERCATOR/PHYSICS/HINDCAST'
ocean_validation_dir   = 'data/OSTIA'
# ------------------------------ variable names ------------------------------ #
sst_name  = 'thetao'
uo_name   = 'uo'
vo_name   = 'vo'
ssh_name  = 'zos'
```

La idea de estructurar los programas de esta manera es para permitir nuevos desarrollos, como por ejemplo agregar un categoría adicional de pronóstico (e.g biogeoquímica) con sus propias rutas/archivos y metodos (e.g *load_biogeo*).

---

### Notas sobre como cambiar el modelo de pronóstico (e.g de Mercator a CROCO)

Para usar un dataset distinto (e.g salidas CROCO) hay que crear una función nueva en el archivo *load.py* que pueda leer el archivo crudo y transformarlo a un formato utilizable por el paquete. Adicionalmente hay que editar algunas funciones de lectura para usar la nueva estrategia de carga. No es complejo y lo explico brevemente a continuación:

La mayoría de los scripts dependen de dos funciones llamadas *forecast_path(...)* y *load_forecast_path(...*) ambas dentro del archivo *load.py.* La primera tiene como objetivo encontrar la ruta para un tipo de pronóstico y fecha de interés, y la segunda tiene como propósito cargar en la memoria el archivo netCDF indicando también el tipo de pronóstico (**ocean, atm, wave**). Respecto al funcionamiento de estas técnicas se puede decir que la primera función simplemente busca el último archivo disponible en la carpeta de cada pronóstico y la segunda se encarga de cargar la data y modificar los nombres o estructura de los datos. La función *load_forecast_path(...)* es una función que se aprovecha de funciones específicas para cargar datasets, como por ejemplo *load_mercator* o *load_wrf*. En el caso de querer implementar una nueva fuente de datos para el oceanograma o mapas, como croco, sería necesario crear una función *load_croco(...)* y habría que editar la función *load_forecast_path(...)* para que utilice dicha función en el pronóstico océanico.

Un ejemplo de uso de estas funciones para un análisis cualquiera sería algo así:

```python
import os
from params import *
from load import forecast_path, load_forecast_data

os.chdir('/ruta/al/directorio/de/trabajo/con/este/paquete')

target_date  = '2023-12-04'
atm_path     = forecast_path(target_date, 'atm')
ocean_path   = forecast_path(target_date, 'ocean')
wave_path    = forecast_path(target_date, 'wave')

atm_data     = load_forecast_data(atm_path, 'atm')     # <-- Acá un xarray dataset listo para ser utilizado
ocean_data   = load_forecast_data(ocean_path, 'ocean') # <-- Acá un xarray dataset listo para ser utilizado
wave_data    = load_forecast_data(wave_path, 'wave')   # <-- Acá un xarray dataset listo para ser utilizado

ocean_data['sst'].iloc(leadtime=0).plot()              # <-- Plot simple de la condición inicial
```

Los archivos grillados cargados en las variables **atm_data, ocean_data** y **wave_data** están construidos con una estructura que sigue un formato como el siguiente:

```bash
<xarray.Dataset>
Dimensions:   (leadtime: 265, lat: 296, lon: 342)
Coordinates:
  * leadtime  (leadtime) datetime64[ns] 2023-12-04 ... 2023-12-15
    time      datetime64[ns] 2023-12-04
  * lat       (lat) float64 -36.29 -36.25 -36.21 -36.16 ... -23.23 -23.18 -23.14
  * lon       (lon) float64 -80.39 -80.35 -80.31 -80.26 ... -65.28 -65.23 -65.19
Data variables:
    var1       (leadtime, lat, lon) float32 0.0 0.0 0.0 0.0 ... 0.0 0.0 0.0 0.0
    var2       (leadtime, lat, lon) float32 0.0 0.0 0.0 0.0 ... 0.0 0.0 0.0 0.0
    var3       (leadtime, lat, lon) float32 0.0 0.0 0.0 0.0 ... 0.0 0.0 0.0 0.0
Attributes:
    regrid_method:  bilinear

```

Donde se puede apreciar que es un archivo netCDF de variables cuyas coordenadas son la latitud (**lat**), longitud (**lon**), el tiempo de inicio (**time**) y el tiempo de pronóstico (**leadtime)**. **E****l paquete funciona unicamente con grillas rectangulares** donde la latitud y la longitud son arrays unidimensionales. Usualmente las salidas de modelos numéricos (como WRF y CROCO) utilizan grillas curvilíneas o no-estructuradas por lo que sería necesario un regrillado como requisito. Para ver como hacerlo directamente desde python se puede revisar la función *load_wrf*  en *load.py* donde se regrilla la información meteorológica a una grilla rectangular para luego utilizarse en las rutinas de visualización.

---

### Notas sobre el pronóstico de mareas

El pronóstico de mareas es el único que funciona un poco distinto, esto porque el modelo océanico MERCATOR no contempla las mareas en su simulación, de manera que el nivel del mar simulado sólo contempla la variabilidad dinámica/termodinámica del fluido (compresión/expansión térmica, presión atmosférica, corrientes geostróficas, etc). Para el computo de las mareas se utiliza el producto TPXO7 el cuál está construido a partir de un modelo océanico global barotrópico que simula sólo la respuesta océanica ante el forzante astronómico ([https://www.tpxo.net/]()). Este modelo permite obtener la amplitud y fase de 10 armónicos mareales para cualquier lugar del planeta a 0.25°x0.25° de resolución.

Para este producto no se realizan mapas por lo que su uso se concentra únicamente en el oceanograma, cuyos datos se crean en la rutina *create_localforecast.py.* En dicho programa se definen las funciones que rescatan los datos de los distintos datasets y se crea la tabla del oceanograma, contemplando por supuesto las mareas. En este caso se hace uso también del paquete pytides para transformar los armónicos mareales a la serie de tiempo del pronóstico. También se realizan las correcciones nodales, las cuáles corrigen los armónicos por movimientos astronómicos relacionados con la fecha del calendario (los armónicos son independientes del tiempo, por lo menos en la escala de ¿años/decadas/siglos?, y la corrección nodal viene a corregir algunos cambios de amplitud y fase asociados a la fecha del pronóstico en cuestión (no conozco muy bien la física detrás de esto pero funciona))).

---

### Notas sobre la creación del oceanograma y creación de los mismos para un punto cualquiera

Como se comentaba anteriormente en el pronóstico de mareas, los datos del oceanograma se crean con el script *create_localforast.py*. Este script consta de dos métodos, el primero es responsable de cargar los datos y crear las tablas de pronóstico de todas las localidades aprovechandose del segundo método que rescata los datos para un único punto. El cálculo de la tabla para múltiples localidades se realiza en paralelo, por lo que depende del número de trabajos a utilizar (*n_jobs*). Por defecto al correr el script desde el terminal, este toma la tabla de localidades que está en archivo *data/COASTAL_POINTS.csv,* pero también es posible crear tablas para puntos nuevos agregandólos en el COASTAL_POINTS.csv o bien llamando a los métodos puntualmente. Si es que la opción de guardado está activada (*save=Tru*e por defecto), las tablas de pronóstico se guardarán en la carpeta *tmp/.* como archivos .csv para cada localidad.

Un segundo script llamado *local_forecast.py* ayuda a visualizar el oceanograma. En este script está la función que toma el nombre de una localidad, su latitud, longitud y la fecha de inicio del pronóstico y crea una figura con el oceanograma en números y colores. Si se corre este script directamente desde el terminal se utilizarán los parámetros entregados en la parte final del script, siendo útil para probar como se ve el oceanograma en puntos no considerados en la tabla. Ojo que el script intentará tomar el archivo guardado en *tmp/* si es que existe, por lo que cuidado al repetir la figura de un pronóstico antiguo.

Finalmente, un último desarrollo fue el oceanograma imprimible para las caletas, el cuál está controlado por el script *local_forecast_print.py* dicho programa se encarga de tomar las figuras creadas con el script *local_forecast.py* y transformarlas a **.pdf** con una orientación vertical, fácil para llegar e imprimir.

---

### Notas sobre el funcionamiento operacional del paquete

Con respecto al funcionamiento operacional que tiene el paquete actualmente en el CEAZA, el archivo *run.py* es el más relevante ya que permite correr todos los métodos de los demás scripts. Este programa se puede correr directamente desde la consola con uno de los siguientes comandos:

```bash
python3 run.py
./run.py
```

Para que el segundo comando funcione el script tiene que tener permisos de ejecución (*chmod +x run.py*) y la primera línea del archivo tiene que especificar la ruta al ejecutable python por utilizar. La estructura del archivo es simple: se importan los métodos de cada script en particular y se corre cada uno despues del otro siempre y cuando la llave esté activada. Al inicio del archivo se encuentran las llaves de que metodos correr. Respecto a esto, los intentos de generar diagnósticos y validaciones en tiempo real son los que están menos depurados y pueden tener errores. Sería bueno si alguien se motiva a desarrollar herramientas de ese tipo, luego con la estructura de este paquete no sería tan dificil implementar las visualizaciones de forma operacional. Las llaves que abren los métodos de visualización y creación de pronósticos locales/regionales están funcionando bastante bien y sólo presentan errores cuando el archivo general de pronóstico no se encuentra (poco usual y dificil de controlar).

El paquete está actualmente funcional en el CEAZA, ejecutándose en la ruta **lucas@ip5.ceazamet.cl:/home/lucas/CEAZAMAR_FORECAST** donde el archivo *run.py* se ejecuta diariamente a través del *crontab* de la cuenta. Si uno desea correr el paquete manualmente, o en una distinta máquina, lo que se debe hacer es instalar el ambiente python con el archivo *.yml* para luego activar el ambiente (*conda activate nombreambiente*) y correr desde el terminal los scripts deseados, específicando las rutas correctas en *params.py* con las correctas funciones de lectura de datos en *load.py.*

---

### Notas finales sobre la sincronizacion y copia de archivos entre maquinas del CEAZA

Como los mapas de pronóstico y datos del oceanograma se utilizan como insumos en la webapp y páginas web del instituto es necesario sincronizar los datos creados en la maquina local con una maquina remota donde los desarrolladores web del ceaza (Carlo, Pablo?) puedan utilizarlos. Para esto está el archivo *post_request.py* el cuál tiene un par de funciones para sincronizar los datos entre máquinas. La función principal *transfer_ceazamar(...)* se encarga de sincronizar los archivos desde la maquina local con el servidor web **@ip1.ceazamet.cl** donde sigue la "posta" hasta los productos web. El método simplemente llama al sistema y corre comandos linux como *rsync* y *scp* por lo que para que funcione correctamente en este paquete el usuario tiene que poder conectarse con la maquina remota sin clave-ssh.
