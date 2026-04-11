Struttura elemento parte testuale del dataset

All’inizio viene dato un contesto generale, il nome dello steakHolder e il numero di utenti del sistema.
Vengono definite le vnf con nomi e ordinamento della catena, viene esplicitato se devono essere in cloud o in edge.
Successivamente vengono definite le changing properties, nella frase viene nominata la proprietà da applicare 
tra logging, privacy, security, caching, compression, encoding e decoding. Viene anche definita la posizione 
nella catena della proprietà da applicare. Infine vengono definiti i vincoli QoS utilizzando parole come “mandatory ” 
per i vincoli Hard e “it is prefered” per i vincoli Soft.
Per ogni vnf viene definito una vnfxUser con range di utenti che va da 1 fino al numero definito all’inizio. 
