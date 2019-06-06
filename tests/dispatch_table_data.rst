# Headings here are filesystem paths (X = "exists")        # Headings here are URL paths, rows represent the dispatch results (ok = okay, ui = unindexed, - = missing, @ = canonical path).
===== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
index bar.spt bar.txt bar.txt.spt %bar.spt bar/ bar/index  /                      /bar                      /bar/                      /bar.txt                      /bar.txt/
===== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
  #   1 file
  X      _       _         _          _      _      _      ok index               -                         -                          -                             -
  _      X       _         _          _      _      _      ui /                   ok bar.spt                -                          ok bar.spt                    -
  _      _       X         _          _      _      _      ui /                   -                         -                          ok bar.txt                    -
  _      _       _         X          _      _      _      ui /                   -                         -                          ok bar.txt.spt                -
  _      _       _         _          X      _      _      ok %bar.spt (bar='')   ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok %bar.spt (bar='bar.txt')   ok %bar.spt (bar='bar.txt/')
  _      _       _         _          _      X      _      ui /                   ui bar/ @/bar/            ui bar/                    -                             -
  _      _       _         _          _      _      X      ui /                   ok bar/index @/bar/       ok bar/index               -                             -
  #   2 files
  X      X       _         _          _      _      _      ok index               ok bar.spt                -                          ok bar.spt                    -
  X      _       X         _          _      _      _      ok index               -                         -                          ok bar.txt                    -
  X      _       _         X          _      _      _      ok index               -                         -                          ok bar.txt.spt                -
  X      _       _         _          X      _      _      ok index               ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok %bar.spt (bar='bar.txt')   ok %bar.spt (bar='bar.txt/')
  X      _       _         _          _      X      _      ok index               ui bar/ @/bar/            ui bar/                    -                             -
  X      _       _         _          _      _      X      ok index               ok bar/index @/bar/       ok bar/index               -                             -
  _      X       X         _          _      _      _      ui /                   ok bar.spt                -                          ok bar.txt                    -
  _      X       _         X          _      _      _      ui /                   ok bar.spt                -                          ok bar.txt.spt                -
  _      X       _         _          X      _      _      ok %bar.spt (bar='')   ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.spt                    ok %bar.spt (bar='bar.txt/')
  _      X       _         _          _      X      _      ui /                   ok bar.spt                ui bar/                    ok bar.spt                    -
  _      X       _         _          _      _      X      ui /                   ok bar.spt                ok bar/index               ok bar.spt                    -
  _      _       X         X          _      _      _      ui /                   -                         -                          ok bar.txt                    -
  _      _       X         _          X      _      _      ok %bar.spt (bar='')   ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      _       X         _          _      X      _      ui /                   ui bar/ @/bar/            ui bar/                    ok bar.txt                    -
  _      _       X         _          _      _      X      ui /                   ok bar/index @/bar/       ok bar/index               ok bar.txt                    -
  _      _       _         X          X      _      _      ok %bar.spt (bar='')   ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  _      _       _         X          _      X      _      ui /                   ui bar/ @/bar/            ui bar/                    ok bar.txt.spt                -
  _      _       _         X          _      _      X      ui /                   ok bar/index @/bar/       ok bar/index               ok bar.txt.spt                -
  _      _       _         _          X      X      _      ok %bar.spt (bar='')   ui bar/ @/bar/            ui bar/                    ok %bar.spt (bar='bar.txt')   ok %bar.spt (bar='bar.txt/')
  _      _       _         _          X      _      X      ok %bar.spt (bar='')   ok bar/index @/bar/       ok bar/index               ok %bar.spt (bar='bar.txt')   ok %bar.spt (bar='bar.txt/')
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
#ndex bar.spt bar.txt bar.txt.spt %bar.spt bar/ bar/index  /                      /bar                      /bar/                      /bar.txt                      /bar.txt/
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
  #   3 files
  X      X       X         _          _      _      _      ok index               ok bar.spt                -                          ok bar.txt                    -
  X      X       _         X          _      _      _      ok index               ok bar.spt                -                          ok bar.txt.spt                -
  X      X       _         _          X      _      _      ok index               ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.spt                    ok %bar.spt (bar='bar.txt/')
  X      X       _         _          _      X      _      ok index               ok bar.spt                ui bar/                    ok bar.spt                    -
  X      X       _         _          _      _      X      ok index               ok bar.spt                ok bar/index               ok bar.spt                    -
  X      _       X         X          _      _      _      ok index               -                         -                          ok bar.txt                    -
  X      _       X         _          X      _      _      ok index               ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      _       X         _          _      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok bar.txt                    -
  X      _       X         _          _      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok bar.txt                    -
  X      _       _         X          X      _      _      ok index               ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  X      _       _         X          _      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok bar.txt.spt                -
  X      _       _         X          _      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok bar.txt.spt                -
  X      _       _         _          X      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok %bar.spt (bar='bar.txt')   ok %bar.spt (bar='bar.txt/')
  X      _       _         _          X      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok %bar.spt (bar='bar.txt')   ok %bar.spt (bar='bar.txt/')
  _      X       X         X          _      _      _      ui /                   ok bar.spt                -                          ok bar.txt                    -
  _      X       X         _          X      _      _      ok %bar.spt (bar='')   ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      X       X         _          _      X      _      ui /                   ok bar.spt                ui bar/                    ok bar.txt                    -
  _      X       X         _          _      _      X      ui /                   ok bar.spt                ok bar/index               ok bar.txt                    -
  _      X       _         X          X      _      _      ok %bar.spt (bar='')   ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  _      X       _         X          _      X      _      ui /                   ok bar.spt                ui bar/                    ok bar.txt.spt                -
  _      X       _         X          _      _      X      ui /                   ok bar.spt                ok bar/index               ok bar.txt.spt                -
  _      X       _         _          X      X      _      ok %bar.spt (bar='')   ok bar.spt                ui bar/                    ok bar.spt                    ok %bar.spt (bar='bar.txt/')
  _      X       _         _          X      _      X      ok %bar.spt (bar='')   ok bar.spt                ok bar/index               ok bar.spt                    ok %bar.spt (bar='bar.txt/')
  _      _       X         X          X      _      _      ok %bar.spt (bar='')   ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      _       X         X          _      X      _      ui /                   ui bar/ @/bar/            ui bar/                    ok bar.txt                    -
  _      _       X         X          _      _      X      ui /                   ok bar/index @/bar/       ok bar/index               ok bar.txt                    -
  _      _       X         _          X      X      _      ok %bar.spt (bar='')   ui bar/ @/bar/            ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      _       X         _          X      _      X      ok %bar.spt (bar='')   ok bar/index @/bar/       ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      _       _         X          X      X      _      ok %bar.spt (bar='')   ui bar/ @/bar/            ui bar/                    ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  _      _       _         X          X      _      X      ok %bar.spt (bar='')   ok bar/index @/bar/       ok bar/index               ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
#ndex bar.spt bar.txt bar.txt.spt %bar.spt bar/ bar/index  /                      /bar                      /bar/                      /bar.txt                      /bar.txt/
#==== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================
  #   4 files
  X      X       X         X          _      _      _      ok index               ok bar.spt                -                          ok bar.txt                    -
  X      X       X         _          X      _      _      ok index               ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      X       X         _          _      X      _      ok index               ok bar.spt                ui bar/                    ok bar.txt                    -
  X      X       X         _          _      _      X      ok index               ok bar.spt                ok bar/index               ok bar.txt                    -
  X      X       _         X          X      _      _      ok index               ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  X      X       _         X          _      X      _      ok index               ok bar.spt                ui bar/                    ok bar.txt.spt                -
  X      X       _         X          _      _      X      ok index               ok bar.spt                ok bar/index               ok bar.txt.spt                -
  X      X       _         _          X      X      _      ok index               ok bar.spt                ui bar/                    ok bar.spt                    ok %bar.spt (bar='bar.txt/')
  X      X       _         _          X      _      X      ok index               ok bar.spt                ok bar/index               ok bar.spt                    ok %bar.spt (bar='bar.txt/')
  X      _       X         X          X      _      _      ok index               ok %bar.spt (bar='bar')   ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      _       X         X          _      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok bar.txt                    -
  X      _       X         X          _      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok bar.txt                    -
  X      _       X         _          X      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      _       X         _          X      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      _       _         X          X      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  X      _       _         X          X      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  -      X       X         X          X      _      _      ok %bar.spt (bar='')   ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  -      X       X         X          _      X      _      ui /                   ok bar.spt                ui bar/                    ok bar.txt                    -
  -      X       X         X          _      _      X      ui /                   ok bar.spt                ok bar/index               ok bar.txt                    -
  -      X       _         X          X      X      _      ok %bar.spt (bar='')   ok bar.spt                ui bar/                    ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  -      X       _         X          X      _      X      ok %bar.spt (bar='')   ok bar.spt                ok bar/index               ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  -      _       X         X          X      X      _      ok %bar.spt (bar='')   ui bar/ @/bar/            ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  -      _       X         X          X      _      X      ok %bar.spt (bar='')   ok bar/index @/bar/       ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  #   5 files
  X      X       X         X          X      _      _      ok index               ok bar.spt                ok %bar.spt (bar='bar/')   ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      X       X         X          _      X      _      ok index               ok bar.spt                ui bar/                    ok bar.txt                    -
  X      X       X         X          _      _      X      ok index               ok bar.spt                ok bar/index               ok bar.txt                    -
  X      X       X         _          X      X      _      ok index               ok bar.spt                ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      X       X         _          X      _      X      ok index               ok bar.spt                ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      X       _         X          X      X      _      ok index               ok bar.spt                ui bar/                    ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  X      X       _         X          X      _      X      ok index               ok bar.spt                ok bar/index               ok bar.txt.spt                ok %bar.spt (bar='bar.txt/')
  X      _       X         X          X      X      _      ok index               ui bar/ @/bar/            ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      _       X         X          X      _      X      ok index               ok bar/index @/bar/       ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      X       X         X          X      X      _      ok %bar.spt (bar='')   ok bar.spt                ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  _      X       X         X          X      _      X      ok %bar.spt (bar='')   ok bar.spt                ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  #   6 files
  X      X       X         X          X      X      _      ok index               ok bar.spt                ui bar/                    ok bar.txt                    ok %bar.spt (bar='bar.txt/')
  X      X       X         X          X      _      X      ok index               ok bar.spt                ok bar/index               ok bar.txt                    ok %bar.spt (bar='bar.txt/')
===== ======= ======= =========== ======== ==== =========  =====================  ========================  =========================  ============================  ================================

Notes:
------

  * Philosophy: 'most specific wins'
    * exact matches beat non-exact matches
    * requesting /foo.html will check/return approximately: foo.html, foo.html.spt, foo.spt, foo.html/, %*.html.spt, %*.spt

  * Note that bar/ and bar/index in the above are mutually exclusive since bar/index implies the existence of bar/
  * There should be 2^5 * 3 lines data lines: on/off for the files except the last two have only 3 possibilites: [ bar/, bar/index, nothing ]

Future work:
============

  * Potentially interesting files:
    * %bar/
    * %bar/index
    * %bar/baz.spt

