# Fase di Pulizia dell’Audio  
**Obiettivo, Metodo e Interpretazione dei Risultati**

La fase di pulizia serve a **standardizzare i brani prima dell’estrazione delle feature**, mantenendo però **intatto il contenuto musicale**.  
Nel contesto della techno questo punto è fondamentale: l’obiettivo non è migliorare il brano dal punto di vista estetico, ma renderlo **coerente, confrontabile e stabile dal punto di vista timbrico**, così che la successiva analisi geometrica — traiettorie nel manifold, clustering, grafi di stati — dipenda dalle caratteristiche musicali reali, e non da differenze tecniche di mix o master.

---

# Metodo di Pulizia  
La pipeline applica pochi passaggi mirati, volutamente poco invasivi:

### **1. Caricamento a 44.1 kHz**  
Garantisce una risoluzione sufficiente per catturare i transienti e le componenti ritmiche tipiche del genere.

### **2. Conversione in mono (scelta intenzionale)**  
Non è pensata per l’ascolto, ma per ridurre la variabilità introdotta dall’immagine stereo.  
In questo modo le differenze tra tracce riflettono **timbro, ritmo e struttura**, non scelte di panning o effetti laterali.

### **3. Normalizzazione del livello**  
Allinea l’energia dei brani ed evita che differenze di volume influenzino le feature.  
Nel manifold, una variazione di volume non deve essere scambiata per una differenza timbrica.

### **4. Filtro passa-banda leggero (30–18 kHz)**  
Rimuove soltanto le componenti più estreme dello spettro:  
- sub profondissimo sotto i 30 Hz  
- “aria" ultra-alta oltre i 18 kHz  

Queste zone sono spesso instabili o irrilevanti per la descrizione timbrica. Il filtro non è un intervento creativo, ma un modo per avvicinare i brani a uno spazio comune.

### **5. Nessun denoise**  
A differenza delle prime versioni del pipeline, non viene applicata alcuna riduzione del rumore.  
Il denoise rischia infatti di introdurre artefatti, soprattutto nelle parti più dense o aggressive della techno.

---

# Confronto Raw vs Clean  
**Cosa viene misurato**

Per verificare che la pulizia non alteri la natura del brano, vengono confrontate varie statistiche tra versione “raw” e “clean”:

- **RMS** (energia complessiva)  
- **Spectral Centroid** + deviazione standard  
- **Spectral Bandwidth**  
- **Spectral Rolloff (85%)**  
- **Spectral Flatness**  
- **MFCC 1–5** (prime componenti della firma timbrica)  

Questi parametri descrivono la **forma dello spettro** e la sua evoluzione nel tempo, cioè la base stessa della rappresentazione nel manifold.

---

# Interpretazione dei Risultati

L’impatto della pulizia sulle statistiche è molto contenuto:

- l’**energia** varia di meno del **10%**  
- il **centroid** cambia di pochi Hz → brillantezza quasi invariata  
- la **bandwidth** resta stabile → nessuna perdita reale di sub o alte  
- la **flatness** non si altera → la texture della techno rimane intatta  
- gli **MFCC 2–5** variano di meno di **±1.5** → timbro praticamente identico  

L’unico valore che cambia più visibilmente è **MFCC1**, legato all’energia logaritmica: è normale, perché riflette la normalizzazione del livello.

**Conclusione:**  
La versione “clean” è quasi indistinguibile dalla “raw” sul piano timbrico, ma è più regolare e più adatta alla rappresentazione geometrica.

---

# Perché la Pulizia è Essenziale per il Modello

Lo scopo non è migliorare artisticamente il suono, ma **eliminare le fonti di variabilità non musicali**:

- differenze di volume  
- sub o alte fuori scala dovute al mix  
- casualità introdotte dal panorama stereo  
- residui marginali non utili alla descrizione timbrica  

Questo allineamento permette di ottenere:

- traiettorie più stabili nel tempo  
- feature paragonabili tra brani diversi  
- un manifold meno rumoroso  
- cluster più robusti  
- un grafo degli stati più leggibile  

Il risultato è una rappresentazione coerente che conserva tutto ciò che è **musicalmente rilevante**.

---

# Sintesi Finale

La fase di pulizia:

- mantiene invariata la timbrica del brano  
- rimuove la varianza non informativa  
- uniforma il dataset  
- prepara i brani a un’analisi complessa e comparativa  
- non interviene sul contenuto artistico  

È una pulizia **scientifica**, non estetica:  
si limita a togliere ciò che disturba la lettura geometrica, lasciando intatto ciò che definisce realmente il brano.

---
