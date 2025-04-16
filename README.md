# Geneva Weather Data Collection

## Lancez le projet:

1. Ouvrez un terminal et placez-vous dans le dossier `docker` :
   ```bash
   cd docker
   ```

2. Lancez les services avec Docker :
   ```bash
   docker-compose up --build
   ```

3. Ouvrez le navigateur et accédez à :
   ```
   http://localhost:8050/home
   ```
   
## Introduction:

Welcome to the Geneva Weather Data Collection project! This initiative focuses on gathering comprehensive weather data specifically tailored to the Geneva region. The project is essential for various applications such as urban planning, agriculture, and renewable energy projects. In this README, we'll outline the project's goals, data collection methods, and storage options.

## Goals:

The primary objective of this project is to collect a wide range of weather data pertinent to Geneva. This includes luminosity, radiance, temperature, and precipitation. By collecting such data, we aim to provide valuable insights for stakeholders involved in urban planning, agriculture, and renewable energy initiatives in the Geneva area.

## Data Collection:

We employ robust web scraping techniques to gather weather data from reputable sources that provide accurate and up-to-date information specific to the Geneva region. Our data collection focuses on:

1. **Luminosity:** We capture the intensity of sunlight, essential for understanding daylight patterns and assessing solar energy potential in Geneva.
   
2. **Radiance:** Gathering information on electromagnetic radiation emission helps in assessing solar radiation levels in the Geneva area, crucial for various applications.

3. **Temperature:** Recording ambient temperature variations is vital, impacting daily life, agriculture, and energy consumption in Geneva.

4. **Precipitation:** Monitoring rainfall and snowfall levels is significant for water resource management and urban infrastructure planning in Geneva.

## Storage Options:

For storing the collected weather data, we utilize an internal relational database hosted by one of our group members. This choice offers several advantages:

- **Efficient Data Management:** A relational database enables us to manage structured data efficiently, facilitating easy querying and ensuring data integrity through relationships and constraints.

- **Scalability:** As our dataset grows, a relational database provides scalability, accommodating an increasing volume of weather data seamlessly.

- **Data Security:** Hosting our database internally ensures greater control over data security and access, mitigating risks associated with external storage solutions.

## Conclusion:

The Geneva Weather Data Collection project is dedicated to providing comprehensive and reliable weather information tailored specifically for the Geneva area. Through meticulous web scraping techniques and utilizing a robust relational database for storage, we aim to empower stakeholders with actionable insights for informed decision-making in urban planning, agriculture, and renewable energy initiatives in Geneva.

Thank you for your interest in our project! For further details and inquiries, please refer to the project documentation. 🏙️🌱
