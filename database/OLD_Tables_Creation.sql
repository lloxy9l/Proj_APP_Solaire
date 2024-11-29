Create table Mesures  (
		idmesure int PRIMARY KEY,
        irradiance float,
        temperature float,
        precipitation float,
        humidite float,
        date_collect DATETIME
);

Create table PointsGPS (
    idpoint int PRIMARY KEY,
    latitude float,
    longitude float
)

Create table Zone(
    idzone int PRIMARY KEY,
    nom VARCHAR(50),
    rayon int,
    origin_latitude float,
    origin longitude float
)

Create table appartient (
    idzone int,
    idpoint int,
    CONSTRAINT pkappartient PRIMARY KEY(idzone,idpoint)
)
