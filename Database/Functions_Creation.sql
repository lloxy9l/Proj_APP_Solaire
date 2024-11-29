DELIMITER //

CREATE FUNCTION get_temperature_for_point(point_id INT) RETURNS VARCHAR(255)
BEGIN
    DECLARE temp VARCHAR(255);
    SELECT temperature INTO temp FROM mesures WHERE id = point_id;
    RETURN temp;
END //

DELIMITER ;

DELIMITER //

CREATE FUNCTION get_ensoleillement_for_point(point_id INT) RETURNS VARCHAR(255)
BEGIN
    DECLARE ensoleillement VARCHAR(255);
    SELECT ensoleillement INTO ensoleillement FROM mesures WHERE id = point_id;
    RETURN ensoleillement;
END //

DELIMITER ;

DELIMITER //

CREATE FUNCTION get_irradiance_for_point(point_id INT) RETURNS VARCHAR(255)
BEGIN
    DECLARE irradiance VARCHAR(255);
    SELECT irradiance INTO irradiance FROM mesures WHERE id = point_id;
    RETURN irradiance;
END //

DELIMITER ;

DELIMITER //

CREATE FUNCTION get_precipitation_for_point(point_id INT) RETURNS VARCHAR(255)
BEGIN
    DECLARE precipitation VARCHAR(255);
    SELECT precipitation INTO precipitation FROM mesures WHERE id = point_id;
    RETURN precipitation;
END //

DELIMITER ;

DELIMITER //

CREATE FUNCTION get_weather_for_date_and_point(point_id INT, collect_date VARCHAR(255)) RETURNS TABLE (
    temperature VARCHAR(255),
    ensoleillement VARCHAR(255),
    irradiance VARCHAR(255),
    precipitation VARCHAR(255)
)
BEGIN
    RETURN (
        SELECT temperature, ensoleillement, irradiance, precipitation
        FROM mesures
        WHERE id = point_id AND date_collecte = collect_date
    );
END //

DELIMITER ;

-- Mean weather values between two dates

DELIMITER //
CREATE FUNCTION get_mean_weather_values(date1 VARCHAR(255), date2 VARCHAR(255)) RETURNS TABLE (
    mean_temperature FLOAT,
    mean_ensoleillement FLOAT,
    mean_irradiance FLOAT,
    mean_precipitation FLOAT
)
BEGIN
    RETURN (
        SELECT
            AVG(CAST(temperature AS FLOAT)) AS mean_temperature,
            AVG(CAST(ensoleillement AS FLOAT)) AS mean_ensoleillement,
            AVG(CAST(irradiance AS FLOAT)) AS mean_irradiance,
            AVG(CAST(precipitation AS FLOAT)) AS mean_precipitation
        FROM mesures
        WHERE date_collecte BETWEEN date1 AND date2
    );
END //

DELIMITER ;

--
