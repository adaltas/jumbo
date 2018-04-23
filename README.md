# Générateur d'environnement de développement Hadoop-HDP

Ce projet permet de paramêtrer et déployer un cluster Hadoop sur un environnement local. Il s'appuye sur le projet [vagrant-hdp-cluster](http://gitlab.adaltas.com/stages/vagrant-hdp-cluster) et permet aux utilisateurs de paramêtrer le cluster sans avoir à comprendre ce dernier.

La paramétrisation se fait via une CLI où il est possible de paramétrer :
- les machines virtuelles (hôtes) :
    - nom
    - IP
    - RAM
    - disque
- les services :
    - repartition sur les machines