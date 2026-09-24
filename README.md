# Robo Kyle

Everything Kyle wears or plugs in, and the server that ties it together.

**Factum** (`factum/`) is the central backend: a Node server + React site that listens to every device, logs, and
is the only thing that writes settings. Every other folder is a product that talks to Factum or to another
product.

Band Viewer: [band/software/viewer/index.html](band/software/viewer/index.html) (open from disk; shows the current prints)
