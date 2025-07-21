# 🚦 Transport ATM Monitor

**Transport ATM Monitor** è un componente custom per Home Assistant per monitorare i trasporti ATM in tempo reale.

---

## 📋 Descrizione

Questo componente integra i dati ATM in Home Assistant, permettendo di visualizzare il tempo di attesa in reale time degli autobus\tram di una fermata.


---

## 📁 Struttura del progetto

custom_components/
└── transportatm/
    ├── __init__.py
    ├── manifest.json
    ├── sensor.py
    ├── binary_sensor.py
README.md
LICENSE

---

## 🛠️ Installazione manuale

1. Copiare la cartella `transportatm` in `custom_components` nella tua installazione di Home Assistant  
2. Riavviare Home Assistant  
3. Inserire nel `configuration.yaml`:

``yaml
transportatm:
  api_key: "LA_TUA_API_KEY"
  # altre opzioni


📲 Installazione tramite HACS (se supportato)
1. Aggiungere il repository custom a HACS
2. Installare il componente da HACS
3. Riavviare Home Assistant

🖼️ Screenshot e Istruzioni di Configurazione
Dopo aver installato il componente, segui questi passaggi per aggiungere l'integrazione:

1. Vai su Dispositivi e Servizi in Home Assistant.
2. Clicca su Aggiungi Integrazione e cerca "TransportATM".
3. Nel popup che appare, inserisci:
  -  La linea del trasporto che vuoi monitorare
  -  Il codice della fermata, che puoi recuperare direttamente dal sito ATM cercando la fermata desiderata

<img width="388" height="373" alt="image" src="https://github.com/user-attachments/assets/c4252dd5-173e-4488-81a9-14000ac530c2" />

<img width="877" height="448" alt="image" src="https://github.com/user-attachments/assets/d7e83f09-cae7-41cd-9398-2816970b7496" />

4. Conferma con OK: l'integrazione creerà un sensore personalizzabile che mostra i dati in tempo reale.

<img width="567" height="520" alt="image" src="https://github.com/user-attachments/assets/30d10aae-2080-4fdb-ab60-e7edd17c518f" />


Aggiornamento Sensore
È possibile forzare l'aggiornamento del sensore usando il comando entity_update.
Se si imposta un intervallo di aggiornamento (update interval) di 60 secondi, si può usare questo comando per aggiornare i dati manualmente.

Nota:
Non è consigliato impostare un update interval inferiore a 30 secondi per evitare un eccesso di richieste che potrebbero essere interpretate come traffico da bot dal server ATM.

