# 🚦 Transport ATM Monitor

**Transport ATM Monitor** è un componente custom per Home Assistant per monitorare i trasporti ATM in tempo reale.

---

## 📋 Descrizione

Questo componente integra i dati ATM in Home Assistant, permettendo di visualizzare il tempo di attesa in reale time degli autobus\tram di una fermata.

<img width="358" height="126" alt="image" src="https://github.com/user-attachments/assets/8ab6f4b8-8279-4284-baa0-bd9378e7c15e" />


## 🛠️ Installazione manuale

1. Copiare la cartella `transportatm` in `custom_components` nella tua installazione di Home Assistant dentro il percorso \config\custom_components\transportatm
3. Riavviare Home Assistant  


📲 Installazione tramite HACS 
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

🧩 Esempio di Card Personalizzata in Lovelace
Questo è un esempio di card realizzata con button-card e layout-card, che mostra due linee ATM in un'unica visualizzazione. Ogni linea è colorata dinamicamente in base al tempo di arrivo:
- Verde se mancano più di 8 minuti
- Arancione se mancano tra 5 e 8 minuti
- Rosso se mancano meno di 5 minuti o il mezzo è in arrivo

<details>
<summary>💡 Clicca qui per vedere l'esempio completo della Card Lovelace</summary>

```yaml
(type: custom:layout-card
layout_type: custom:grid-layout
cards:
  - type: custom:button-card
    name: 🚋 Fermata Bus
    styles:
      card:
        - height: 110px
        - width: 350px
        - border-radius: 15px
        - padding: 10px 15px
        - font-size: 20px
        - text-shadow: 0px 0px 5px black
        - text-transform: capitalize
        - margin-left: "-10px"
      grid:
        - grid-template-areas: '"n" "Linea1" "Linea2"'
        - grid-template-columns: 1fr
        - grid-template-rows: min-content min-content min-content
      name:
        - font-weight: bold
        - font-size: 23px
        - color: goldenrod
        - align-self: start
        - justify-self: start
        - padding-bottom: 4px
      custom_fields:
        Linea1:
          - justify-self: start
          - text-align: left
          - font-size: 16px
          - padding-bottom: 4px
        Linea2:
          - justify-self: start
          - text-align: left
          - font-size: 16px
    custom_fields:
      Linea1: |
        [[[ 
          let stato = states['sensor.transportatm211335_2']?.state || 'N/A';
          let colore = 'gray';
          if (stato.toLowerCase().includes('arrivo')) {
            colore = 'red';
          } else {
            let minuti = parseInt(stato);
            if (!isNaN(minuti)) {
              if (minuti > 8) colore = 'limegreen';
              else if (minuti > 4) colore = 'orange';
              else colore = 'red';
            }
          }
          return `<ha-icon icon="mdi:bus-clock" style="width: 20px; height: 20px; color: ${colore}; margin-right: 5px;"></ha-icon>
                  <span>Linea 1: <span style="color: ${colore}">${stato}</span></span>`;
        ]]]
      Linea2: |
        [[[ 
          let stato = states['sensor.transportatm9211335_2']?.state || 'N/A';
          let colore = 'gray';
          if (stato.toLowerCase().includes('arrivo')) {
            colore = 'red';
          } else {
            let minuti = parseInt(stato);
            if (!isNaN(minuti)) {
              if (minuti > 8) colore = 'limegreen';
              else if (minuti > 4) colore = 'orange';
              else colore = 'red';
            }
          }
          return `<ha-icon icon="mdi:bus-clock" style="width: 20px; height: 20px; color: ${colore}; margin-right: 5px;"></ha-icon>
                  <span>Linea 2: <span style="color: ${colore}">${stato}</span></span>`;
        ]]]
grid_options:
  columns: 9
  rows: 2
layout:
  grid-template-columns: 60% 1
  grid-template-rows: auto
  grid-template-areas: |
    "main notify update")


