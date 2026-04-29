# lab_infrastructure

Gemeinsame Infrastruktur fuer die Projekte im `nmt_lab`-Workspace.

Der erste Baustein ist `lab_infrastructure.run_config` mit den oeffentlichen
Funktionen `run(...)`, `run_cli(...)` und `write_run_config(...)` fuer
standardisierte `*_config.yaml`-Dateien mit Pydantic-Validierung sowie
Timestamp- und Git-Metadaten.


## VS-Code-Tasks

Radon-Task-Muster verwenden `<P>` fuer eines der Workspace-Projekte
`translator`, `data_preprocessor`, `model_based_curation` oder
`lab_infrastructure`:

- `radon raw <P> src`
- `radon lloc production src report <P>`
- `radon lloc production src total <P>`

Fuer Unterpakete Radon direkt auf dem gewuenschten Pfad ausfuehren:

```powershell
.\.venv-tools\Scripts\python.exe -m radon raw translator/src/translator/training
```

`pytest all` fuehrt alle Tests des ausgewaehlten Projektordners aus.

