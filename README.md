🔍 Analizador de Followers – Ley de Benford (Instagram Bot Detector)

Este proyecto analiza seguidores de una cuenta de Instagram utilizando la Ley de Benford para detectar patrones anómalos que sugieren actividad no orgánica (bots, compras de seguidores, granjas digitales, etc.).
El análisis se ejecuta en una interfaz Streamlit y genera un reporte profesional, gráfico y exportable en Excel.

🧠 ¿Cómo funciona?

El sistema obtiene:

Los seguidores de una cuenta usando los endpoints web de Instagram

Para cada seguidor, obtiene su número total de followers

Extrae el primer dígito de cada conteo

Compara la distribución real con la distribución esperada por la Ley de Benford

Calcula:

diferencias porcentuales

desviación total

umbrales de anomalía

probabilidad Benford por observación

Exporta un informe Excel automático

Genera gráficos y dashboards en Streamlit

✨ Características principales

🚀 Análisis estadístico real basado en Ley de Benford

🧩 Scraping paginado de hasta 550 seguidores

🔄 Reintentos automáticos por bloqueo o respuestas no-JSON

🔥 Protección contra soft-ban (delay dinámico)

📊 Visualización avanzada con Matplotlib

📂 Exportación profesional a Excel

🧪 Logs completos de ejecución

📦 Requisitos

Instalar dependencias:
