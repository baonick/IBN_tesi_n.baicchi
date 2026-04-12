Struttura elemento parte testuale del dataset

All’inizio viene dato un contesto generale, il nome dello steakHolder e il numero di utenti del sistema.
Vengono definite le vnf con nomi e ordinamento della catena, viene esplicitato se devono essere in cloud o in edge.
Successivamente vengono definite le changing properties, nella frase viene nominata la proprietà da applicare 
tra logging, privacy, security, caching, compression, encoding e decoding. Viene anche definita la posizione 
nella catena della proprietà da applicare. Infine vengono definiti i vincoli QoS utilizzando parole come “mandatory ” 
per i vincoli Hard e “it is prefered” per i vincoli Soft.
Per ogni vnf viene definito una vnfxUser con range di utenti che va da 1 fino al numero definito all’inizio. 







Script

all'interno della cartella script ci sono 4 programmi 
script.sh serve per creare in automatico la gerarchia delle cartelle degli intenti 
creaDataset.py serve per creare il dataset in formato json direttamente dalle cartelle degli intenti
train.py serve per l'addestramento di un modello tramite il dataset generato da creaDataset.py, si possono modificare diversi parametri compreso la scelta del modello 
tester.py serve per eseguire il modello addestrato inserendo un intento nuovo, genera codice in fatti prolog
