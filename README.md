# 🏠 Système de Maison Intelligente

## 📌 Description du projet
Ce projet consiste à développer un système de maison intelligente basé sur un microcontrôleur (Arduino MKR WAN 1310). 
Il intègre plusieurs fonctions domotiques essentielles : sécurité incendie, automatisation de l’éclairage et détection de présence.

L’objectif est de simuler un environnement domestique intelligent capable de réagir automatiquement à son environnement afin d’améliorer
la sécurité, le confort et l’efficacité énergétique.

---

## 🔥 Sécurité incendie
Les incendies domestiques représentent une cause majeure de sinistres. Une détection rapide d’une flamme permet une intervention précoce et 
limite la propagation des dégâts.

Le capteur **DFR0076 de DFRobot** est utilisé pour détecter les rayonnements infrarouges caractéristiques d’une flamme. Il possède un angle de 
détection d’environ **60°** et une portée d’environ **1 mètre**.

Lorsqu’une flamme est détectée, le système déclenche immédiatement :
- un buzzer émettant un signal sonore à **1 000 Hz**
- une **LED rouge d’alerte**

Cette combinaison assure une alerte locale immédiate et visible.

---

## 💡 Automatisation de l’éclairage
La gestion intelligente de l’éclairage permet de réduire significativement la consommation énergétique dans un bâtiment.

Le capteur de luminosité **DFR0026** mesure l’intensité lumineuse ambiante sur une échelle analogique allant de **0 à 1023**.

Lorsque la luminosité descend en dessous d’un seuil de **300**, le système active automatiquement une **LED d’ambiance jaune/orange**
afin de compenser le manque de lumière naturelle.

---

## 🚶 Détection de présence
La détection de présence est un élément central des systèmes domotiques, permettant de conditionner des actions telles que l’éclairage automatique, 
la sécurité ou la gestion énergétique.

Dans ce projet, une adaptation a été nécessaire en raison d’une défaillance du module de détection de présence initialement prévu.
Une solution alternative a été mise en place.

---

## ⚙️ Matériel et technologies utilisées
- Arduino MKR WAN 1310  
- Capteur de flamme infrarouge **DFR0076 (DFRobot)**  
- Capteur de luminosité **DFR0026 (DFRobot)**
- Capteur ultrasonic **URM09**
- LED rouge (alerte)  
- LED d’ambiance (jaune/orange)  
- Buzzer (1 000 Hz)  
- Langage **C++ (Arduino IDE)**  

---

## 🎯 Objectifs du projet
- Concevoir un système de maison intelligente fonctionnel  
- Détecter les risques d’incendie en temps réel  
- Automatiser l’éclairage selon la luminosité ambiante  
- Adapter le système en cas de contrainte matérielle  
- Appliquer les bases des systèmes embarqués et de l’IoT  

---

