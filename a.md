# Feature Extraction Pipeline

Questa pipeline trasforma un brano audio in una sequenza di vettori di feature, uno per ogni frame temporale.  
Ogni vettore rappresenta un punto nello “spazio timbrico” del brano: una descrizione matematica di **come suona** quel momento della traccia.  

---

## 1. Input Audio e Parametri STFT

Il segnale viene caricato in mono a:

- sampling rate: `sr = 44100`  
- hop duration: `0.25 s`  
- window duration: `1.0 s`

Da cui derivano:

- $ \text{hop\_length} = \text{sr} \cdot \text{hop\_seconds} $
- $ \text{win\_length} = \text{sr} \cdot \text{win\_seconds} $
- $ n_{\text{fft}} = 2^{\lceil \log_2 (\text{win\_length}) \rceil} $

Si ottiene lo spettrogramma di potenza:

- $ S = |\text{STFT}(y)|^2 $  
- $ S_{\text{amp}} = \sqrt{S} $  
- $ S_{\text{dB}} = 10 \log_{10}(S + 10^{-10}) $

Lo spettrogramma è una mappa tempo–frequenza che descrive “dove va l’energia” del suono in ogni istante.

---

## 2. Timbre Domain — MFCC (40 coefficienti)

Gli MFCC (Mel-Frequency Cepstral Coefficients) sono la spina dorsale della rappresentazione timbrica.

- $ \text{mfcc} \in \mathbb{R}^{40 \times T} $

### **Interpretazione**  
Gli MFCC descrivono *la forma complessiva dello spettro*, cioè il “colore” del suono:

- suono **scuro** vs **brillante**
- **morbido** vs **metallico**
- **chiuso** vs **aperto**
- **armonico** vs **rumoroso**

Sono fondamentali per distinguere ruoli come kick, pad, hi-hat, lead, basso, texture, ecc.  
Nell’analisi timbrica moderna rappresentano la componente più informativa.

---

## 3. Spectral Texture Domain

Questi descrittori catturano la “texture” dello spettro: come è distribuita l’energia, quanto è concentrata, quanto si estende verso le alte frequenze.

### **Spectral Centroid**
$$
c_t = \frac{\sum_f f \, S_{\text{amp}}(f,t)}{\sum_f S_{\text{amp}}(f,t)}
$$

Indica il “baricentro” dello spettro.  
**Interpretazione:** è un buon indicatore di brillantezza. Un hi-hat ha tipicamente centroid molto alto, un kick molto basso.

---

### **Spectral Bandwidth**  
Misura quanto lo spettro è “largo” attorno al centroide.  
**Interpretazione:** distingue suoni focalizzati (es. sinusoidi) da suoni ricchi e complessi (piatti, noise, risuonanti).

---

### **Spectral Rolloff (85%, 95%)**  
Sono frequenze limite che delimitano l’85% o il 95% dell'energia totale.  
**Interpretazione:** utile per capire se l’energia è tutta in basso (kick, bass) o diffusa in alto (piatti, noise, texture digitali).

---

### **Spectral Flatness**
$$
\text{flat}_t = \frac{\text{GM}(S(:,t))}{\text{AM}(S(:,t))}
$$

**Interpretazione:**  
- valore alto → suono simile al rumore bianco  
- valore basso → suono con poche frequenze dominanti (più “tonale”)

È ottimo per distinguere rumore, sibilanti, hi-hat aperti.

---

### **Spectral Flux**  
Misura quanto lo spettro cambia tra frame consecutivi.

**Interpretazione:**  
- alto → attacco, transizione, cambi bruschi  
- basso → suono stabile, sostenuto

Serve a identificare punti in cui il brano “si muove” di più.

---

## 4. Informazione di Disordine e Forma Spettrale

### **4.1 Spettro Normalizzato**

$$
P(f,t) = \frac{S(f,t)}{\sum_f S(f,t) + \varepsilon}
$$

Rende ogni frame un “distributore di probabilità” sulle frequenze.

---

### **4.2 Entropia Spettrale**

$$
H_t = -\sum_f P(f,t)\,\log(P(f,t) + 10^{-10})
$$

(normalizzata tramite $\log(F)$)

**Interpretazione:**  
- vicino a 0 → spettro più ordinato, poche frequenze dominanti  
- vicino a 1 → spettro molto disordinato, simile al rumore

Ottimo per distinguere pad/lead (più ordinati) da rumori o FX.

---

### **4.3 Spectral Crest**

$$
\text{crest}_t = \frac{\max_f S(f,t)}{\text{mean}_f\,S(f,t)}
$$

**Interpretazione:**  
- alto → c’è una frequenza che svetta (suono con picco dominante: fischio, risonanza, armonica forte)  
- basso → spettro più uniforme

---

### **4.4 Spectral Spread**

$$
\text{spread}_t = 
\sqrt{
\sum_f P(f,t)\left(f - c_t\right)^2
}
$$

Misura la varianza dello spettro attorno al centroide.

**Interpretazione:**  
- spread basso → suono compatto e focalizzato  
- spread alto → suono ampio, diffuso, ricco di frequenze

---

## 5. Dynamics Domain — Energia e Transienti

### **RMS**

$$
\text{RMS}_t = \sqrt{\frac{1}{N}\sum_{n} y[n]^2}
$$

L’energia locale del suono.

**Interpretazione:**  
RMS è un indicatore affidabile di “volume percepito”:  
una bassline compressa avrà RMS più alto, mentre un piatto sottile meno.

---

### **Transient Strength**

Una copia coerente del flux, usata come misura specifica della rapidità del cambiamento.

**Interpretazione:**  
captura gli “attacchi”, ovvero momenti in cui un suono inizia bruscamente: kick, snare, clap, transienti di piatti.

---

## 6. Pitch Domain — Chroma Microtonale (24 bin)

Il cromagramma microtonale suddivide l’asse delle frequenze in 24 bande pseudo-armoniche.

$$
\text{chroma}_{k,t}, \quad k = 1,\dots,24
$$

**Interpretazione semplice:**  
Dice **quali zone armoniche sono attive** in un frame.

Serve per distinguere:

- suoni **tonali** (lead, pad, voci, synth melodici)  
- suoni **non tonali** (percussioni, rumori, texture)  

e per individuare centri tonali e movimenti melodici.

---

### **Chroma Concentration**

$$
\text{conc}_t = \max_k \frac{\text{chroma}_{k,t}}{\sum_k \text{chroma}_{k,t} + \varepsilon}
$$

**Interpretazione:**  
Indica quanto la melodia è “focalizzata” su una zona:  
- conc alto → nota chiara, stabile  
- conc basso → suono distribuito / rumoroso / cluster armonico largo

---

## 7. Allineamento Temporale

Per garantire compatibilità fra tutte le feature si tronca ogni matrice alla stessa lunghezza temporale:

$$
T = \min(T_{\text{mfcc}},\, T_{\text{centroid}},\,\dots,\, T_{\text{chroma}})
$$

La traiettoria finale è:

$$
\text{trajectory} \in \mathbb{R}^{T \times d}
$$

---

## 8. Output Finale: Trajectory + Feature Names

La pipeline restituisce:

- **trajectory**: matrice $T \times d$ con il vettore di feature per ogni frame  
- **feature\_names**: elenco dei nomi delle feature, in ordine coerente

Questa traiettoria è la rappresentazione ad alta dimensione del brano.  
Su di essa si costruiscono:

- **stati timbrici** (cluster)  
- **grafo delle transizioni**  
- **entropia degli stati**  
- **entropia delle transizioni**  
- **modularità**  
- **backbone**  
- **complexity fingerprint**  

È qui che il brano diventa finalmente un **sistema dinamico**, modellabile con gli strumenti della teoria dei sistemi complessi.

---
