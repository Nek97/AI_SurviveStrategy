# DEVLOG

[Passo] Rifondazione del progetto in Python
-> [Problema Incontrato] La precedente scelta architetturale in Node.js risultava limitante per la complessità dei calcoli genetici e le matrici matematiche del DNA richieste dall'utente.
-> [Scelta Presa / Cambio di Direzione] Progetto riavviato interamente in Python. Scelto un approccio ibrido: backend FastAPI (Motore ECS custom + logica genetica NumPy) per gestire le prestazioni matematiche e server WebSocket per inviare i tick a un client HTML5 Canvas leggerissimo in JS.

[Passo] Sviluppo ECS Custom e Componenti
-> [Problema Incontrato] Utilizzare librerie ECS Python esterne (come esper) per un progetto con requisiti genetici e matematici così specifici poteva forzare dei workaround o ridurre la flessibilità nel tracciamento genealogico (Kinship) e mescolanza del DNA.
-> [Scelta Presa / Cambio di Direzione] Implementato un piccolo motore ECS proprietario (Registry, Component, System) nel modulo `src/engine/ecs.py`. Questo garantisce il rispetto del DRY e permette di ottimizzare le query sulle entità.

[Passo] Gestione Front-End Web
-> [Problema Incontrato] La renderizzazione su Canvas richiedeva l'elaborazione continua dei frame, rischiando di non essere in sync con i calcoli asincroni del backend Python.
-> [Scelta Presa / Cambio di Direzione] Disaccoppiamento completo: il backend viaggia a una frequenza prefissata di invio (es. `dt=0.1` sec) tramite socket, e il frontend renderizza semplicemente l'ultimo stato inviato. Modificata la geometria per supportare facce testuali e forme poligonali primitive (D4-D20).

[Passo] Astrazione Comportamenti Cibo e Altruismo Suicida
-> [Problema Incontrato] Le interazioni sul cibo necessitavano di una logica "Altruismo Intelligente" non suicida e di combinazioni di ricette.
-> [Scelta Presa / Cambio di Direzione] Modificato InteractionSystem; le entità condividono le risorse o le ricette solo se la loro sopravvivenza base è già garantita (food_collected >= 1). Aggiunta meccanica di Esplorazione e Knowledge per scoprire le ricette ibridando fonti diverse.
