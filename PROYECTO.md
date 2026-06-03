# PyToolkit — Proyecto Completo

## ¿Qué es?

**PyToolkit** es un producto digital: 50+ scripts Python organizados en 5 módulos (archivos, datos, web, PDF, imágenes) con un CLI unificado. Precio: $5 USD one-time. Pagos vía crypto (ETH + SOL).

- Website: https://toolkitpy.com
- GitHub: https://github.com/eonpatrick32-commits/python-productivity-toolkit
- GitHub Pages: https://eonpatrick32-commits.github.io/python-productivity-toolkit/

---

## Estructura del proyecto

```
mny/
├── product/scripts/          ← El producto (50+ scripts Python)
│   ├── toolkit.py            ← CLI unificado
│   ├── file_organizer.py     ← Módulo 1: archivos
│   ├── data_processor.py     ← Módulo 2: datos
│   ├── web_toolkit.py        ← Módulo 3: web
│   ├── pdf_toolkit.py        ← Módulo 4: PDFs
│   ├── image_toolkit.py      ← Módulo 5: imágenes
│   └── payment_monitor.py    ← Monitor de pagos crypto
│
├── site/                     ← Landing page desplegada en Vercel
│   ├── index.html            ← Landing principal (diseño ámbar+navy)
│   ├── tools/index.html      ← 7 herramientas gratuitas interactivas
│   ├── download.html         ← Página de pago/descarga
│   ├── 50-python-one-liners.html ← Artículo viral para SEO/tráfico
│   ├── toolkit.zip           ← Producto empaquetado descargable
│   ├── icon.png / logo.png   ← Branding
│   ├── favicon.ico / favicon.png
│   ├── robots.txt / sitemap.xml ← SEO
│   └── README.md             ← Readme del repo GitHub
│
└── download/                 ← Copia espejo del producto con README
```

---

## Proceso completado

### 1. Producto
- 50+ scripts Python en 5 módulos con docstrings, dry-run y CLI unificado
- Empaquetado en ZIP descargable (41 KB)
- README con ejemplos de uso

### 2. Diseño y branding
- Paleta: deep navy `#080c17` + amber `#f59e0b`
- Tipografía: Outfit (headings) + Inter (body) + JetBrains Mono (código)
- Animaciones: fade-in al scroll (Intersection Observer), hero flotante
- Iconos SVG minimalistas line-art
- Logo personalizado generado por IA
- Tema unificado en las 4 páginas (landing, tools, download, artículo)

### 3. Hosting y dominio
- Dominio: **toolkitpy.com** (comprado en Namecheap)
- Hosting: Vercel (plan Pro, team `metx`)
- Configuración DNS: A record `@` → `76.76.21.21`, CNAME `www` → `cname.vercel-dns.com`
- GitHub: repo creado, código pusheado, Pages habilitado

### 4. SEO
- sitemap.xml, robots.txt
- Canonical URLs (toolkitpy.com)
- Meta tags: og:title, og:description, og:image, og:url
- Twitter card: summary_large_image

### 5. Pagos
- ETH: `0x960b9fe28490153eb0cb50ee9c91e7a9a3977dad`
- SOL: `Dfm3P1Sm6Q5GJPSBVnBQWUeNqZPLoGZXNgqfRdyqVPVF`
- Monitor de pagos vía Blockscout API
- Modelo "pay what you want" con descarga gratuita disponible

### 6. Distribución
- **Dev.to**: Artículo "50 Python One-Liners" publicado
- **Product Hunt**: Launch programado para 4 junio 2026 12:01 AM PST
- **Hacker News**: Post publicado
- **PyCoders Weekly**: Form de sugerencia enviado
- **Reddit**: Cuenta creada, intentos en r/SideProject y r/PythonProjects2
- **Twitter/X**: Cuenta creada
- Página de herramientas gratuitas para atraer tráfico orgánico

---

## Comandos útiles

### Verificar si hay ventas (pagos crypto)
```powershell
cd C:\Users\PC\Documents\mny\product\scripts
python payment_monitor.py --once
```

### Monitoreo continuo (cada 5 minutos)
```powershell
cd C:\Users\PC\Documents\mny\product\scripts
python payment_monitor.py
```

### Verificar manualmente
- ETH: https://etherscan.io/address/0x960b9fe28490153eb0cb50ee9c91e7a9a3977dad
- SOL: https://solscan.io/account/Dfm3P1Sm6Q5GJPSBVnBQWUeNqZPLoGZXNgqfRdyqVPVF

### Desplegar cambios al sitio
```powershell
cd C:\Users\PC\Documents\mny\site
git add -A
git commit -m "Descripción del cambio"
git push origin main
vercel --prod --yes
```

### Probar el producto localmente
```powershell
cd C:\Users\PC\Documents\mny\product\scripts
python toolkit.py --help
python toolkit.py files organize --dir ./demo
python toolkit.py data csv2json --input archivo.csv
python toolkit.py pdf text --input documento.pdf
```

---

## Por hacer / Pendiente

1. **Primera venta** — el objetivo del proyecto ($5 USD)
2. **Product Hunt** — monitorear el launch mañana, responder comentarios, compartir en redes
3. **Reddit** — seguir calentando la cuenta y publicar en r/PythonProjects2 o r/SideProject
4. **Newsletters** — enviar a Python Weekly (pythonweekly.com/submit)
5. **Twitter/X** — publicar hilo con screenshots del CLI
6. **LinkedIn** — publicar artículo/promoción
7. **IndieHackers** — publicar el producto
8. **Email de contacto** — configurar un email real en el sitio para soporte
9. **Google Analytics** — agregar tracking al sitio
10. **Automatizar entrega** — que al recibir pago crypto se envíe el ZIP automáticamente

---

## Datos de cuentas creadas

| Plataforma | Usuario | Notas |
|------------|---------|-------|
| GitHub | eonpatrick32-commits | Repo del proyecto |
| Vercel | metx (nightcoremake7-8831) | Hosting del sitio |
| Namecheap | - | Dominio toolkitpy.com |
| HN | - | Cuenta para postear |
| Reddit | - | Calentando karma |
| Dev.to | - | Artículo publicado |
| Product Hunt | - | Launch programado |
| Twitter/X | - | Para promoción |

---

## Métricas clave

- **ETH recibido**: 0 (al cierre del proyecto)
- **Visitantes**: Sin tracking aún
- **Descargas del ZIP**: Sin tracking aún
