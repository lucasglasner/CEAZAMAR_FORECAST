# Pronóstico CEAZAMAR - Rutinas del oceanograma y plots varios

La presente documentación muestra un resumen de los scripts y como usarlos para visualizar el pronóstico del ceazamar a nivel regional o local para un punto de interés. En primer lugar para tener un idea del funcionamiento del paquete se lista la estructura general de directorios con un breve comentario de que es cada cosa:

```
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
