from pathlib import Path

root = Path(__file__).parent.parent

webDist = root / "src" / "web" / "dist"
docsDist = root / "docs" / "dist"

appTagScript = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1Q0NM417RP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-1Q0NM417RP');
</script>
"""

docsTagScript = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-GX1N1ZZN9T"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-GX1N1ZZN9T');
</script>
"""


def addToApp():
    indexFile = webDist / "index.html"
    indexFile.write_text(
        indexFile.read_text().replace("<body>", f"<body>{appTagScript}")
    )


def addToDocs():
    indexFile = docsDist / "index.html"
    indexFile.write_text(
        indexFile.read_text().replace("<body>", f"<body>{docsTagScript}")
    )


if __name__ == "__main__":
    if webDist.is_dir():
        addToApp()
    if docsDist.is_dir():
        addToDocs()
