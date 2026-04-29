# lab_infrastructure

Gemeinsame Infrastruktur fuer die Projekte im `nmt_lab`-Workspace.

Der erste Baustein ist `lab_infrastructure.run_config` mit den oeffentlichen
Funktionen `run(...)`, `run_cli(...)` und `write_run_config(...)` fuer
standardisierte `*_config.yaml`-Dateien mit Pydantic-Validierung sowie
Timestamp- und Git-Metadaten.

