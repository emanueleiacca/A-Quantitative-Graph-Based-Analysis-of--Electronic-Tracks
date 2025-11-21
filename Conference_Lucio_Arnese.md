# Introduzione

L’idea iniziale nasce da una domanda molto semplice, quasi ingenua:  
*e se il suono potesse essere rappresentato come una nube di punti nello spazio tridimensionale, che si muove nel tempo come una costellazione in evoluzione?*

Da questa intuizione prende forma un progetto sia visivo che analitico: un modo per osservare il canto degli uccelli come una geometria che si dispiega, per tradurre strutture acustiche in traiettorie spaziali, per trattare le vocalizzazioni come forme, pattern e superfici deformabili.

All’inizio i modelli erano quasi dei giocattoli concettuali: una serie di punti mossi da oscillatori che reagivano all’ampiezza e alla frequenza del suono, generando nuvole dinamiche e un po’ astratte.  
La svolta arriva quando ogni punto viene pensato come contenitore di **dati**: valori numerici, descrittori spettrali, informazioni aggiuntive.  
Da quel momento la visualizzazione smette di essere decorativa e diventa un modo per *organizzare e leggere* informazioni complesse.

---

# 1. From Simple Particles to High-Dimensional Data Models

Col tempo i punti non rappresentano più solo posizione e luminosità: ogni frame del suono incorpora decine di descrittori.  
Molti di questi sono noti in analisi audio, ma vale la pena spiegarli in modo semplice:

- **ampiezza** → quanto forte è il suono in quel momento  
- **frequenza dominante** → la nota o altezza percepita  
- **centroide spettrale** → una media ponderata delle frequenze, utile per capire se il suono è più “scuro” o “brillante”  
- **spread / rolloff / cresta** → misure che indicano come si distribuisce l’energia sulle frequenze  
- **entropia, skewness, kurtosis** → statistiche che descrivono l'ordine, la simmetria o la “forma” del contenuto spettrale  
- **flux** → quanto cambia lo spettro da un frame al successivo  

E questo è solo il dominio “classico”.  
A questi si aggiungono:

- **MFCCs** (40 coefficienti) → descrivono il *timbro*, cioè la qualità del suono, non solo la sua altezza  
- **Chroma** microtonale (80–120 bin) → una rappresentazione del *pitch*, più fine rispetto ai 12 semitoni occidentali, adatta ai continui scivolamenti tipici degli uccelli

Mettendo tutto insieme, ciascun frame del canto diventa un vettore molto grande: anche **$120$ dimensioni** o più.  
E siccome il suono è campionato a velocità elevata, si generano migliaia di vettori al minuto.  

A quel punto sorge naturalmente un problema:  
come comprimere tutta questa complessità dentro uno spazio 3D che rimanga leggibile?

---

# 2. Dimensionality Reduction as Spatial Translation

Per “tradurre” spazi ad alta dimensione in una forma comprensibile si ricorre alla riduzione dimensionale, cioè metodi matematici che comprimono i dati preservando — per quanto possibile — la loro struttura interna.

Quattro metodi diventano centrali:

### **• PCA**  
Un metodo lineare che trova gli assi principali di variazione. È utile per avere una visione complessiva, ma può perdere dettagli sottili perché non cattura curvature o relazioni complesse.

### **• ISOMAP**  
Prova a conservare le distanze “lungo la superficie” dei dati, come se si cercasse di appiattire un foglio spiegazzato senza deformarne i disegni. È un modo più fedele di rappresentare strutture annidate o “a forma di manifold”.

### **• t-SNE**  
Specializzato nel mettere in evidenza i gruppi locali: se due punti rappresentano due momenti del canto molto simili, t-SNE tende a metterli vicini. Ottimo per individuare ripetizioni, sillabe ricorrenti o micro-pattern.

### **• UMAP**  
Costruisce una struttura topologica “sfocata” e poi la proietta in basso numero di dimensioni. È spesso più stabile di t-SNE e riesce a descrivere bene l’articolazione delle frasi e dei motivi del canto.

Questi metodi non sono intercambiabili: ciascuno produce una geometria diversa, una lettura diversa dello stesso spazio acustico.  
Il risultato finale — il punto posizionato in 3D — rappresenta quindi *una compressione interpretata* del comportamento sonoro.

In questa visione, le coordinate ridotte diventano lo scheletro del modello.  
Tutto il resto — colore, grandezza, variazioni temporali, codifica dei descrittori — è un livello informativo aggiuntivo che si appoggia su questa struttura.

---

# 3. Spectral Domains and Descriptor Taxonomy

Per dare una forma più chiara alla grande quantità di descrittori raccolti, è utile dividerli in insiemi funzionali.  
Questa classificazione non è solo estetica: serve a capire rapidamente *che tipo di informazione* fornisce ogni valore e *come* contribuisce alla lettura del suono.

La suddivisione che segue è in tre domini, ciascuno caratterizzato da una logica diversa.

---

## **HERTZ-DOMAIN**  
Raccoglie i descrittori espressi in frequenza, quindi misure legate a “dove” cade l’energia sonora. Sono utili per capire l’altezza percepita e il modo in cui il contenuto spettrale si organizza:

- **dominant frequency** → la frequenza più forte in quel frame, percepita spesso come la “nota” del suono  
- **spectral centroid** → una media pesata delle frequenze, che indica se il suono è più grave o più brillante  
- **spectral spread** → quanto le frequenze sono disperse attorno al centroide  
- **rolloff (85% / 95%)** → la frequenza sotto la quale cade la maggior parte dell’energia; usata per capire quanto il suono è concentrato o “esteso” verso l’alto  
- **cepstral pitch** → una stima della periodicità del suono ottenuta tramite l’analisi del “cepstro”, utile per distinguere toni stabili da rumori

---

## **UNITLESS-DOMAIN**  
Contiene descrittori adimensionali che descrivono la forma dello spettro o il modo in cui evolve nel tempo. Sono concetti statistici applicati alle frequenze; in molti casi è più importante la *tendenza* che il valore assoluto.

- **spectral skewness** → indica se lo spettro è “sbilanciato” verso frequenze più alte o più basse  
- **spectral kurtosis** → quanto lo spettro è appuntito o piatto; può segnalare suoni molto focalizzati o molto diffusi  
- **spectral entropy** → misura il disordine: valori alti indicano suoni più “rumorosi”  
- **spectral flux** → quanto cambia lo spettro da un momento al successivo; utile per individuare transizioni o attacchi  
- **crest factor** → rapporto tra picco e livello medio; spesso associato a suoni impulsivi o particolarmente brillanti

---

## **dB-DOMAIN**  
Raccoglie descrittori espressi in decibel, quindi misure associate al peso energetico delle componenti e alla qualità tonale.

- **tonality** → stima di quanto il suono sia “tonale” (simile a una nota) o “rumoroso”  
- **spectral contrast** → differenza tra picchi e valli nello spettro; utile per capire se ci sono armoniche forti  
- **spectral slope** → la pendenza dell’energia lungo le frequenze; può indicare suoni più caldi o più brillanti  
- **harmonic-to-noise ratio** → rapporto tra componenti armoniche e rumore; indica la “pulizia” del suono  
- **spectral flatness** → misura quanto lo spettro è uniforme, cioè quanto assomiglia al rumore bianco

---

Mettendo insieme i tre domini, è possibile leggere in modo completo ciò che accade nel suono:

- **dove** è concentrata l’energia  
- **come** si distribuisce  
- **come** si muove nel tempo  
- **quanto** il suono è armonico o rumoroso  
- **se** il frame è stabile o instabile, transitorio o consolidato  

Raggruppare le feature in domini semantici rende la lettura dei dati più intuitiva: si può capire a colpo d’occhio quali descrittori parlano di brillantezza, quali di stabilità, quali di tonalità, e così via. È un modo efficace per ridurre il caos apparente delle analisi spettrali.

---

# 4. Timbre Domain vs. Pitch Domain

Oltre ai domini spettrali classici, il sistema si basa su due famiglie analitiche centrali: **timbro** e **intonazione**. Sono complementari e insieme descrivono quasi tutto ciò che si percepisce in un suono.

---

## **TIMBRE DOMAIN → MFCCs ($0$–$39$)**  
Gli MFCCs derivano da una trasformazione che comprime lo spettro in un insieme di coefficienti più compatti.  
In termini pratici:

- descrivono l’**involucro spettrale**, cioè la forma generale del suono  
- catturano differenze di **brillantezza**, **asprezza**, **risonanza**, **morbidezza**  
- permettono di distinguere suoni simili nella frequenza ma diversi nella qualità  
- sono molto usati in riconoscimento vocale e bioacustica proprio perché sintetici ma informativi

In breve: gli MFCCs raccontano *che tipo di suono* c’è, a prescindere dalla sua nota.

---

## **PITCH DOMAIN → Chroma (80 microtonal bins)**  
La rappresentazione cromatica tradizionale usa 12 semitoni, ma per il canto degli uccelli è troppo grossolana: molte specie eseguono glissandi, microintervalli, modulazioni fini.  
Per questo si usano 80 (o più) bin microtonali.

I chroma descrivono:

- quali zone di frequenza sono attive  
- come si spostano nel tempo  
- quali “centri tonali” emergono  
- come si ripetono pattern o gesti melodici

In altre parole: il dominio cromatico descrive *dove si muove la melodia*.

---

L’unione dei due domini produce una descrizione completa:

- **timbre** → *che cosa è il suono*  
- **pitch** → *dove sta andando*  

Questo doppio asse rende leggibile sia la struttura armonica sia la sua evoluzione, permettendo di confrontare gesti, motivi e variazioni nel canto in modo molto più fine di quanto consentano le rappresentazioni standard.

---

# 5. TouchDesigner Network – The Visual Machinery

L’infrastruttura sviluppata in TouchDesigner funziona come una sorta di “mappa cittadina”: un reticolo complesso in cui decine e decine di nodi scambiano costantemente dati.  
Ogni flusso rappresenta qualcosa: matrici di MFCC, vettori di chroma, array di descrittori, geometrie tridimensionali, segnali di controllo per l’animazione.  
La struttura complessiva non è un semplice patch grafico, ma un vero ambiente modulare pensato per gestire un grande volume di informazioni in tempo reale.

TouchDesigner si occupa principalmente della parte visiva e operativa:

- **rendering** delle nuvole di punti e delle traiettorie  
- **riproduzione dei dati** come se fossero una timeline  
- **mappatura dei colori** basata sui descrittori selezionati  
- **gestione della camera** per movimenti fluidi e orbitali  
- **sincronizzazione** tra grafici, viste e pannelli  
- **espansione modulare** per aggiungere nuove funzionalità  

Python entra in gioco dall’altro lato: esegue calcoli, preprocessa i descrittori, gestisce file e dataset.  
TouchDesigner diventa così il livello di visualizzazione in tempo reale, mentre Python costituisce la base computazionale.

---

# 6. The Interface

L’interfaccia è progettata per permettere un’esplorazione fluida, quasi tattile, dei dati acustici.  
Ogni elemento serve a mettere in relazione la visualizzazione 3D con le rappresentazioni più tradizionali (spettrogramma, cromagramma, ecc.).

Gli elementi principali includono:

- **una viewport 3D** con una camera che orbita lentamente per mantenere la percezione di profondità  
- **sliders per x/y framing**, utili per centrare o ampliare l’inquadratura  
- **una finestra temporale scalabile**, per focalizzarsi su eventi brevi o osservare strutture a lungo termine  
- **controlli play/pause** per navigare il flusso del canto  
- **colorazione in base ai descrittori**, che consente letture immediate (ad esempio variazioni di brillanza o instabilità)  
- **selettore del metodo di riduzione dimensionale**, così da confrontare PCA, t-SNE, UMAP e ISOMAP in tempo reale  
- **pannelli sincronizzati**: spettrogramma, cromagramma e cepstrogramma avanzano insieme al modello 3D  
- **grafici MFCC e chroma** aggiornati frame-by-frame, per collegare dettagli locali alla struttura globale  

La dimensione del punto (o particella) è controllata dall’ampiezza del segnale, ma questo è solo un default: qualunque descrittore può diventare un driver visivo.  
Si possono quindi evidenziare instabilità, transizioni, variazioni timbriche o nodi tonali modificando un singolo parametro.

---

# 7. A Tool for Research Laboratories

L’intero sistema nasce come strumento di esplorazione, pensato più per offrire nuove prospettive che per sostituire le metodologie tradizionali della bioacustica.  
È, in sostanza, un **micro-laboratorio visivo**, capace di rendere immediatamente percepibili strutture che normalmente rimangono nascoste nei numeri.

Nella visualizzazione tridimensionale:

- **gesti ripetuti** tracciano **curve simili**, riconoscibili a colpo d’occhio  
- **variazioni timbriche** deformano lo spazio MFCC  
- **micro-shift del pitch** si manifestano come torsioni e deviazioni nello spazio Chroma  

L’atto del vedere diventa un atto di analisi: ciò che in forma di dati numerici è difficile da interpretare, in forma di geometria animata diventa intuitivo.

Questo approccio richiama idee di sonificazione inversa, ascolto computazionale e analisi morfospaziale: campi in cui la visualizzazione non è un semplice supporto, ma una vera estensione cognitiva per capire pattern complessi.

---

# 8. Demonstration – Song Thrush in MFCC UMAP

Nel primo esempio viene visualizzata una vocalizzazione di **Turdus philomelos** (Song Thrush) utilizzando lo spazio MFCC ridotto con **UMAP**.  
Il risultato è una serie di **archi tridimensionali** dalla forma sorprendentemente chiara: le frasi del canto appaiono come curve pulite e consistenti, e ogni volta che l’uccello ripete un certo motivo, la traiettoria si ripete quasi identica.  
La riduzione dimensionale non si limita quindi a comprimere i dati: ne rivela la struttura gestuale.

Uno degli aspetti interessanti è la possibilità di confrontare rapidamente le diverse proiezioni dello stesso dataset.  
Con un semplice selettore si passa da:

- **MFCC PCA / t-SNE / ISOMAP / UMAP**  
a  
- **Chroma PCA / t-SNE / ISOMAP / UMAP**

Ciascun metodo mette in risalto proprietà differenti del canto:

- PCA enfatizza le variazioni globali.  
- t-SNE raggruppa bene i gesti simili.  
- ISOMAP conserva i percorsi lungo la "superficie" dei dati.  
- UMAP produce strutture stabili e leggibili nel suo equilibrio tra locale e globale.

Non si tratta di scegliere il “migliore”, ma di ottenere più punti di vista sulla stessa informazione acustica, come osservare un oggetto complesso da angolazioni diverse.

---

# 9. Color Mapping and Descriptor Scaling

L’aspetto cromatico della visualizzazione non è arbitrario: il colore è un canale informativo che può essere assegnato a qualunque descrittore.  
Questo permette di leggere la geometria non solo in termini di forma, ma anche in relazione a proprietà spettrali e dinamiche.

Tra i parametri utilizzati più spesso:

- **spectral centroid** → indica cambiamenti di brillantezza timbrica  
- **spectral spread** → segnala momenti più ricchi o più concentrati  
- **spectral flux** → mette in evidenza transizioni rapide o attacchi  
- **chroma energy concentration** → utile per individuare zone tonali più forti

Al cambio del descrittore, la legenda si **auto-riscalibra** per riflettere il range effettivo del dataset.  
Questo è fondamentale: un descrittore può variare molto in un dataset e pochissimo in un altro, e una scala fissa renderebbe i colori fuorvianti.

Quando la geometria si anima con il colore, la nube di punti diventa una sorta di **mappa termica in movimento**, in cui l'andamento armonico, la brillantezza, la stabilità o l’instabilità emergono visivamente senza bisogno di strumenti statistici.

In questo modo la visualizzazione funziona contemporaneamente come rappresentazione estetica e come strumento diagnostico.

---
# 10. The Real-Time Domain

La visualizzazione opera a **60 FPS**, il che equivale a circa **3600 campioni al minuto** tradotti in punti nello spazio.  
Questa scelta non deriva da un limite tecnico, ma da un criterio percettivo: una frequenza di aggiornamento costante e fluida permette di seguire il movimento della nube senza sfarfallii o discontinuità, rendendo leggibile anche la struttura più complessa.

Il livello computazionale, però, è un’altra storia.  
Quando l’analisi è eseguita offline, non esiste un limite pratico al numero di frame o descrittori elaborabili: dataset da un milione o anche un miliardo di punti sono teoricamente gestibili, dipendendo solo dalla memoria e dalla potenza macchina.

*(COMMENTO MIO)*  
Questa distinzione tra **dominio percettivo** e **dominio analitico** è molto elegante.  
È un principio simile a quello usato nei motori grafici, nelle simulazioni fisiche e nella visualizzazione di big data: il sistema calcola quanto serve per l’analisi, ma mostra all’occhio solo ciò che è utile per comprendere.

---

# 11. Chroma Time-Plane (Preliminary Experiment)

Un esperimento parallelo è il **Chroma Time-Plane**, una rappresentazione che ricorda una sorta di piano roll microtonale.  
Non è ancora una visualizzazione definitiva, ma offre spunti interessanti.

Gli elementi principali:

- i valori **ATBN** (Amp-Tracked Binned Notes) formano **linee orizzontali**, simili ai tasti di un pianoforte ampliato a microintervalli  
- il **centroide spettrale** appare come una curva superiore che scorre nel tempo, mostrando variazioni di brillantezza  
- l’**ampiezza** funge da banda inferiore, utile per evidenziare accenti e dinamiche  
- le **frequenze** sono ridotte di un fattore **$10\times$** per rendere la visualizzazione più compatta e leggibile

Pur essendo una prima versione, la struttura suggerisce una possibile evoluzione verso una vera “mappa microtonale” navigabile.

---

# 12. Interoperability and Modularity

L’intero sistema è progettato per essere aperto e flessibile.  
Piuttosto che imporre formati o procedure rigide, accetta differenti sorgenti e rende facile l’integrazione di nuove feature.

Supporta:

- file audio **WAV/FLAC**  
- matrici **CSV** generate da qualsiasi ambiente  
- descrittori calcolati esternamente (Python, MATLAB, R, ecc.)  
- separazione totale tra **geometria**, **colore**, **metadati** e **animazione**  
- aggiunta di nuovi descrittori senza modificare il nucleo del sistema  

In questo senso si comporta come un **microscopio visivo** per dati acustici:  
la parte ottica (la visualizzazione) è stabile, mentre la parte analitica (i dati e i descrittori) può evolvere liberamente.

---

# Conclusione

*Seeing Birdsong* si colloca a metà tra arte e analisi scientifica:  
un ecosistema visivo che trasforma la vocalizzazione in geometria animata.

Rende visibili:

- la struttura nascosta nel timbro  
- l’organizzazione microtonale del pitch  
- la ripetizione di gesti e motivi  
- le morfologie del comportamento acustico  
- le transizioni che caratterizzano le specie  

È uno strumento, un metodo e allo stesso tempo un modo diverso di avvicinarsi al suono:  
**ascoltare attraverso la visione**.

>Per come è concepito, questo framework potrebbe diventare un riferimento nella visualizzazione bioacustica: un sistema espandibile che integra analisi tradizionali con clustering automatico, embedding neurali e modelli self-supervised come wav2vec2, permettendo nuovi livelli di interpretazione.


---
