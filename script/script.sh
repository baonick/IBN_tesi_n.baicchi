#!/bin/bash

#script per creare le cartelle

# Controlla se è stato inserito un numero
if [ -z "$1" ]; then
  echo "Errore: Devi specificare il numero di cartelle da creare."
  echo "Uso: ./genera_dataset.sh <numero>"
  exit 1
fi

NUMERO=$1

# Ciclo per creare le N cartelle
for (( i=8; i<=NUMERO; i++ ))
do
  NOME_CARTELLA="intent$i"
  
  # Crea la cartella
  mkdir -p "$NOME_CARTELLA"
  
  # Crea i tre file vuoti all'interno della cartella
  touch "$NOME_CARTELLA/$NOME_CARTELLA.pl"
  touch "$NOME_CARTELLA/$NOME_CARTELLA.txt"
  touch "$NOME_CARTELLA/output.txt"
  
  echo "Creata cartella: $NOME_CARTELLA con i relativi file."
done

echo "Operazione completata! Sono state create $NUMERO cartelle."
