-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Hôte : db
-- Généré le : ven. 04 avr. 2025 à 09:18
-- Version du serveur : 9.2.0
-- Version de PHP : 8.2.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `projet_solarx`
--

-- --------------------------------------------------------

--
-- Structure de la table `2026_solarx_consommation`
--

CREATE TABLE `2026_solarx_consommation` (
  `id_consommation` int NOT NULL,
  `nom_commune` varchar(50) NOT NULL,
  `consommation` decimal(10,3) NOT NULL COMMENT 'MWh',
  `annee` int NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `2026_solarx_consommation`
--

ALTER TABLE 2026_solarx_consommation ADD COLUMN population INT;
INSERT INTO `2026_solarx_consommation` (`id_consommation`, `nom_commune`, `consommation`, `annee`,`population`) VALUES
(1, 'Archamps', 1140.277, 2022, 2542),
(2, 'Archamps', 4796.931, 2023, 2542),
(3, 'Beaumont', 90.915, 2022, 10650),
(4, 'Beaumont', 174.672, 2023, 10650),
(5, 'Bossey', 7.509, 2022, 947),
(6, 'Bossey', 227.474, 2023, 947),
(7, 'Chênex', 76.271, 2022, 730),
(9, 'Chevrier', 261.864, 2022, 677),
(10, 'Chevrier', 256.744, 2023, 677),
(11, 'Collonges-sous-Salève', 1046.133, 2022, 3919),
(12, 'Collonges-sous-Salève', 140.520, 2023, 3919),
(35, 'Annemasse', 2611.195, 2023, 38314),
(14, 'Dingy-en-Vuache', 5.448, 2023, 756),
(15, 'Feigères', 134.380, 2022, 1791),
(16, 'Feigères', 473.756, 2023, 1791),
(17, 'Jonzier-Épagny', 56.309, 2022, 835),
(18, 'Jonzier-Épagny', 131.637, 2023, 835),
(19, 'Neydens', 490.629, 2022, 2227),
(20, 'Neydens', 461.492, 2023, 2227),
(36, 'Ville-la-Grand', 1549.131, 2023, 9196),
(23, 'Saint-Julien-en-Genevois', 5096.385, 2022, 15925),
(24, 'Saint-Julien-en-Genevois', 1159.495, 2023, 15925),
(40, 'Ambilly', 829.329, 2023, 6166),
(26, 'Savigny', 37.357, 2023, 1970),
(27, 'Valleiry', 432.406, 2022, 5090),
(28, 'Valleiry', 245.963, 2023, 5090),
(38, 'Gaillard', 2611.195, 2023, 11054 ),
(37, 'Cranves-Sales', 1459.363, 2023, 7182),
(41, 'Bernex', 286.000, 2023, 1428),
(39, 'Monnetier', 735.329, 2023, 2333),
(34, 'Vulbens', 2093.743, 2023, 1698),
(42, 'Cartigny', 30.000, 2023, 695),
(47, 'Genève', 2723398.000, 2023, 524379),
(48, 'Champfromier', 350.844, 2023, 676),
(49, 'Minzier', 545.469, 2023, 1051),
(50, 'Farges', 567.267, 2023, 1093),
(51, 'Étrembières', 1305.804, 2023, 2516),
(52, 'Amancy', 1177.092, 2023, 2268),
(53, 'Boëge', 941.466, 2023, 1814),
(54, 'Jussy', 653.421, 2023, 1259),
(55, 'Nangy', 772.791, 2023, 1489),
(56, 'Carouge', 11937.0, 2023, 23000),
(57, 'Pers-Jussy', 1089.9, 2023, 2100),
(58, 'Collex-Bossy', 845.97, 2023, 1630),
(59, 'Loisin', 778.5, 2023, 1500),
(60, 'Scientrier', 726.6, 2023, 1400),
(61, 'Sergy', 1038.0, 2023, 2000),
(62, 'Pregny-Chambésy', 2076.0, 2023, 4000),
(63, 'Saint-André-de-Boëge', 259.5, 2023, 500),
(64, 'Challex', 830.4, 2023, 1600),
(65, 'Arenthon', 986.1, 2023, 1900),
(66, 'Ferney-Voltaire', 5138.1, 2023, 9900),
(67, 'Bonne', 1660.8, 2023, 3200),
(68, 'Meyrin', 12975.0, 2023, 25000),
(69, 'Lélex', 114.18, 2023, 220),
(70, 'Éloise', 622.8, 2023, 1200),
(71, 'Viry', 2595.0, 2023, 5000),
(72, 'Choulex', 519.0, 2023, 1000),
(73, 'Confignon', 2595.0, 2023, 5000),
(74, 'Chézery-Forens', 181.65, 2023, 350),
(75, 'Pougny', 363.3, 2023, 700),
(76, 'Prévessin-Moëns', 4411.5, 2023, 8500),
(77, 'Laconnex', 415.2, 2023, 800),
(78, 'Plan-les-Ouates', 6228.0, 2023, 12000),
(79, 'Le Grand-Saconnex', 6228.0, 2023, 12000),
(80, 'Faucigny', 467.1, 2023, 900),
(81, 'Aire-la-Ville', 622.8, 2023, 1200),
(82, 'Corsier (GE)', 1038.0, 2023, 2000),
(83, 'Puplinge', 1038.0, 2023, 2000),
(84, 'Lucinges', 674.7, 2023, 1300),
(85, 'Contamine-sur-Arve', 1816.5, 2023, 3500),
(86, 'Marcellaz', 622.8, 2023, 1200),
(87, 'Chêne-Bougeries', 6747.0, 2023, 13000),
(88, 'Monnetier-Mornex', 1210.827, 2023, 2333),
(89, 'Andilly', 467.1, 2023, 900),
(90, 'Russin', 259.5, 2023, 500),
(91, 'Collonge-Bellerive', 4411.5, 2023, 8500),
(92, 'Saint-Cergues', 1712.7, 2023, 3300),
(93, 'Valserhône', 5449.5, 2023, 10500),
(94, 'Machilly', 519.0, 2023, 1000),
(95, 'Confort', 363.3, 2023, 700),
(96, 'Meinier', 1038.0, 2023, 2000),
(97, 'Collonges', 622.8, 2023, 1200),
(98, 'Bonneville', 6228.0, 2023, 12000),
(99, 'Lancy', 17127.0, 2023, 33000),
(100, 'Avusy', 674.7, 2023, 1300),
(101, 'Vernier', 18165.0, 2023, 35000),
(102, 'Le Sappey', 155.7, 2023, 300),
(103, 'Bons-en-Chablais', 2854.5, 2023, 5500),
(104, 'Thoiry', 235, 2023, 453),
(105, 'Presinge', 386, 2023, 745),
(106, 'Satigny', 2306, 2023, 4449),
(107, 'Saint-Pierre-en-Faucigny', 3937, 2023, 7600),
(108, 'Anières', 1252, 2023, 2417),
(109, 'Veyrier', 6176, 2023, 11901),
(110, 'Genthod', 1450, 2023, 2800),
(111, 'Soral', 499, 2023, 963),
(112, 'Arthaz-Pont-Notre-Dame', 858, 2023, 1657),
(113, 'Péron', 1502, 2023, 2900),
(114, 'Fillinges', 1832, 2023, 3537),
(115, 'Gy', 259, 2023, 500),
(116, 'Présilly', 518, 2023, 1000),
(117, 'Troinex', 1480, 2023, 2858),
(118, 'Bellevue', 2072, 2023, 4000),
(119, 'Reignier-ésery', 4196, 2023, 8100),
(120, 'Vers', 518, 2023, 1000),
(121, 'La Roche-sur-Foron', 5802, 2023, 11200),
(122, 'Chancy', 881, 2023, 1700),
(123, 'Cologny', 3125, 2023, 6037),
(124, 'Onex', 9842, 2023, 19000),
(125, 'Dardagny', 932, 2023, 1800),
(126, 'Saint-Jean-de-Gonville', 1058, 2023, 2042),
(127, 'Bardonnex', 1319, 2023, 2547),
(128, 'La Muraz', 546, 2023, 1055),
(129, 'Veigy-Foncenex', 2090, 2023, 4035),
(130, 'Vétraz-Monthoux', 5501, 2023, 10618),
(131, 'Arbusigny', 590, 2023, 1139),
(132, 'Perly-Certoux', 1714, 2023, 3310),
(133, 'Vandœuvres', 1476, 2023, 2851),
(134, 'Saint-Genis-Pouilly', 7540, 2023, 14558),
(135, 'Clarafond-Arcine', 545, 2023, 1053),
(136, 'Cornier', 761, 2023, 1468),
(137, 'Ornex', 2540, 2023, 4903),
(138, 'Juvigny', 329, 2023, 634),
(139, 'Thônex', 8750, 2023, 16888),
(140, 'Avully', 907, 2023, 1750),
(141, 'Chêne-Bourg', 4967, 2023, 9588),
(142, 'Léaz', 459, 2023, 887),
(143, 'Crozet', 1219, 2023, 2354);

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `2026_solarx_consommation`
--
ALTER TABLE `2026_solarx_consommation`
  ADD PRIMARY KEY (`id_consommation`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `2026_solarx_consommation`
--
ALTER TABLE `2026_solarx_consommation`
  MODIFY `id_consommation` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=144;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
